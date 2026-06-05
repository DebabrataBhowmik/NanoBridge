#!/usr/bin/env python3
import sys, os, math, json
import numpy as np
import awkward as ak
import uproot
import ROOT

# Optional: correctionlib
try:
    import correctionlib
    from correctionlib.schemav2 import CorrectionSet
except Exception:
    correctionlib = None
    CorrectionSet = None

# ------------------------------
# Helpers
# ------------------------------
def load_cset(json_path):
    if correctionlib is None:
        print(f"[warn] correctionlib not available; '{json_path}' will be ignored (identity corrections).")
        return None
    if not os.path.exists(json_path):
        print(f"[warn] corrections JSON '{json_path}' not found. Using identity corrections.")
        return None
    with open(json_path, "r") as f:
        data = json.load(f)
    return CorrectionSet.schema().load(data)

def eval_safe(cset, name, *args, default=1.0):
    if cset is None:
        return default
    try:
        return cset[name].evaluate(*args)
    except Exception:
        return default

def ak_to_list(arr, dtype=np.float32):
    return ak.to_list(ak.values_astype(arr, dtype))

def ak_to_list_int(arr, dtype=np.int32):
    return ak.to_list(ak.values_astype(arr, dtype))

def bool_to_bit(arr_bool, bit):
    # arr_bool: jagged or flat of 0/1
    return ak.values_astype(arr_bool, np.uint64) * (1 << bit)

def pick_first_present(arrdict, names, default=None):
    for n in names:
        if n in arrdict:
            return arrdict[n]
    return default

def or_reduce_bools(candidates):
    # candidates: list of awkward boolean arrays (same length), return OR across those present
    out = None
    for c in candidates:
        if c is None:
            continue
        c_bool = ak.values_astype(c, np.int8)
        out = c_bool if out is None else (ak.values_astype(out, np.int8) | c_bool)
    if out is None:
        return None
    return out

# ------------------------------
# Trigger mapping
# ------------------------------
MU17PHO30_NAMES = [
    "HLT_Mu17_Photon30_IsoCaloId",     # your primary
    "HLT_Mu17_Photon30",               # variant without suffix
    "HLT_Mu17_Photon30_L1",            # L1-seeded variants
    "HLT_Mu17_Photon30_CaloId",
    "HLT_Mu17_Photon30_CaloIdIso",
]
ISOMU_NAMES = [
    "HLT_IsoMu27",                     # common Run2/Run3 single-muon
    "HLT_IsoMu24",
    "HLT_Mu27",                        # sometimes used
]

def hlt_bitfield_from_nano(arrdict, events_keys):
    # Try exact-name branches first
    hlt_mu17pho30 = or_reduce_bools([arrdict.get(n, None) for n in MU17PHO30_NAMES if n in events_keys])
    hlt_isomu     = or_reduce_bools([arrdict.get(n, None) for n in ISOMU_NAMES if n in events_keys])

    # If still None, attempt pattern match over all HLT_* keys present
    if hlt_mu17pho30 is None:
        mu17_like = [k for k in events_keys if k.startswith("HLT_Mu17_Photon30")]
        hlt_mu17pho30 = or_reduce_bools([arrdict.get(k, None) for k in mu17_like])

    if hlt_isomu is None:
        # prefer IsoMu27 pattern, else any IsoMu24
        iso27 = [k for k in events_keys if k.startswith("HLT_IsoMu27")]
        iso24 = [k for k in events_keys if k.startswith("HLT_IsoMu24")]
        mu27  = [k for k in events_keys if k.startswith("HLT_Mu27")]
        pref = iso27 or iso24 or mu27
        hlt_isomu = or_reduce_bools([arrdict.get(k, None) for k in pref])

    # Build bitfield
    n_ev = len(arrdict.get("event", []))
    #zeros = ak.zeros(n_ev, dtype=np.uint64)
    zeros = np.zeros(n_ev, dtype=np.uint64)
    bitfield = zeros
    if hlt_mu17pho30 is not None:
        bitfield = bitfield | bool_to_bit(hlt_mu17pho30, 8)
    if hlt_isomu is not None:
        bitfield = bitfield | bool_to_bit(hlt_isomu, 19)
    return bitfield

# ------------------------------
# Main
# ------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser(description="NanoAOD(v15) → miniTree for xAna with correctionlib + robust HLT.")
    parser.add_argument("-i","--input", required=True)
    parser.add_argument("-o","--output", default="miniTree.root")
    parser.add_argument("--era", default="Run3_2024")
    parser.add_argument("--variation", default="Nominal")
    parser.add_argument("--isMC", action="store_true")
    # Placeholder JSONs — replace with real payloads
    parser.add_argument("--mujson", default="corrections/muon_rochester_placeholder.json")
    parser.add_argument("--phjson", default="corrections/photon_energy_placeholder.json")
    parser.add_argument("--jetjson", default="corrections/jet_jerc_placeholder.json")
    parser.add_argument("--no-muon-pt-corr", action="store_true")
    parser.add_argument("--no-pho-energy-corr", action="store_true")
    parser.add_argument("--no-jet-corr", action="store_true")
    args = parser.parse_args()

    fin = uproot.open(args.input, xrootd=True)
    events = fin["Events"]
    events_keys = events.keys()

    # Load correction sets (placeholders are fine — identity if missing)
    mu_cset  = None if args.no_muon_pt_corr else load_cset(args.mujson)
    ph_cset  = None if args.no_pho_energy_corr else load_cset(args.phjson)
    jet_cset = None if args.no_jet_corr else load_cset(args.jetjson)

    # TODO: set to real correction names in your JSONs
    MU_CORR_NAME = "rochester_k"   # evaluate(eta, phi, q, pt, nTrackerLayers, rand, era)
    PH_EN_NAME   = "pho_energy"    # evaluate(eta, r9, pt, syst) syst in {nom,stat_up,stat_dn,syst_up,syst_dn,gain_up,gain_dn,rho_up,rho_dn,phi_up}
    JER_SF_NAME  = "jer_sf"        # evaluate(eta, pt, rho, syst) syst in {nom,up,down}
    JEC_UNC_NAME = "jec_unc"       # evaluate(eta, pt) → relative uncertainty (fraction)

    # Build list of branches to read
    need = [
        "event","run","luminosityBlock",
        "fixedGridRhoFastjetAll","PV_npvsGood",
        # Muons
        "nMuon","Muon_pt","Muon_eta","Muon_phi","Muon_mass","Muon_charge",
        "Muon_pfRelIso03_all","Muon_pfRelIso03_chg","Muon_sip3d",
        "Muon_isGlobal","Muon_isTracker","Muon_isPFcand",
        "Muon_nStations","Muon_nTrackerLayers","Muon_nPixelHits","Muon_nMatches",
        "Muon_dxy","Muon_dz",
        # Photons
        "nPhoton","Photon_pt","Photon_eta","Photon_phi","Photon_mass",
        "Photon_r9","Photon_hoe","Photon_sieie","Photon_electronVeto",
        "Photon_sieip","Photon_e2x2","Photon_e5x5",
        # Jets
        "nJet","Jet_pt","Jet_eta","Jet_phi","Jet_mass",
        "Jet_neHEF","Jet_neEmEF","Jet_chHEF","Jet_chEmEF","Jet_muEF",
        "Jet_chMult","Jet_neMult","Jet_jetId",
    ]
    # add all present HLT_* booleans
    need += [k for k in events_keys if k.startswith("HLT_")]

    if args.isMC:
        need += [
            "genWeight","Pileup_nTrueInt",
            "nGenPart","GenPart_pdgId","GenPart_pt","GenPart_eta","GenPart_phi","GenPart_mass","GenPart_genPartIdxMother",
            "nLHEPart","LHEPart_pdgId","LHEPart_pt","LHEPart_eta","LHEPart_phi","LHEPart_mass",
        ]

    avail = [k for k in need if k in events_keys]
    arr = events.arrays(avail, how=dict)

    # Event-level
    run   = arr.get("run", ak.Array([]))
    lumi  = arr.get("luminosityBlock", ak.Array([]))
    event = arr.get("event", ak.Array([]))
    rho   = ak.values_astype(arr.get("fixedGridRhoFastjetAll", ak.zeros_like(event, dtype=np.float32)), np.float32)
    rhoAll= rho
    isPVGood = (arr.get("PV_npvsGood", ak.zeros_like(event)) > 0)

    # HLT bitfield for xAna
    HLTEleMuX = hlt_bitfield_from_nano(arr, events_keys)

    # Muons
    mu_pt  = arr.get("Muon_pt", ak.Array([]))
    mu_eta = arr.get("Muon_eta", ak.Array([]))
    mu_phi = arr.get("Muon_phi", ak.Array([]))
    mu_m   = arr.get("Muon_mass", ak.zeros_like(mu_pt))
    mu_q   = arr.get("Muon_charge", ak.zeros_like(mu_pt))
    mu_isG = arr.get("Muon_isGlobal", ak.zeros_like(mu_pt))
    mu_isT = arr.get("Muon_isTracker", ak.zeros_like(mu_pt))
    mu_isPF= arr.get("Muon_isPFcand", ak.zeros_like(mu_pt))
    mu_nSta= arr.get("Muon_nStations", ak.zeros_like(mu_pt))
    mu_nLay= arr.get("Muon_nTrackerLayers", ak.zeros_like(mu_pt))
    mu_nPix= arr.get("Muon_nPixelHits", ak.zeros_like(mu_pt))
    mu_nMat= arr.get("Muon_nMatches", ak.zeros_like(mu_pt))
    mu_dxy = arr.get("Muon_dxy", ak.zeros_like(mu_pt))
    mu_dz  = arr.get("Muon_dz", ak.zeros_like(mu_pt))
    mu_iso_all = arr.get("Muon_pfRelIso03_all", ak.zeros_like(mu_pt))
    mu_iso_chg = arr.get("Muon_pfRelIso03_chg", ak.zeros_like(mu_pt))
    mu_sip3d   = arr.get("Muon_sip3d", ak.zeros_like(mu_pt))

    have_mu_corr = (mu_cset is not None) and (MU_CORR_NAME in getattr(mu_cset, "_corrections", {})) and (not args.no_muon_pt_corr)
    if have_mu_corr:
        rng = np.random.default_rng(123456)
        counts = ak.num(mu_pt)
        rnd = ak.unflatten(rng.random(ak.sum(counts).to_numpy()), counts)
        def mu_k(eta, phi, q, pt, nlay, r):
            return eval_safe(mu_cset, MU_CORR_NAME, float(eta), float(phi), int(q), float(pt), int(nlay), float(r), args.era, default=1.0)
        k = ak.Array([[ mu_k(e,p,qq,pt,nl,rr) for e,p,qq,pt,nl,rr in zip(row_eta,row_phi,row_q,row_pt,row_nlay,row_r) ]
                       for row_eta,row_phi,row_q,row_pt,row_nlay,row_r in zip(mu_eta,mu_phi,mu_q,mu_pt,mu_nLay,rnd)])
    else:
        k = ak.ones_like(mu_pt, dtype=np.float32)

    mu_pt_corr = mu_pt * k
    mu_en_corr = ak.values_astype(np.sqrt((mu_pt_corr*np.cosh(mu_eta))**2 + mu_m**2), np.float32)
    mu_type_bits = (ak.values_astype(mu_isG, np.int32)*2) + (ak.values_astype(mu_isT, np.int32)*4) + (ak.values_astype(mu_isPF, np.int32)*32)
    mu_pfchiso03 = mu_iso_chg * mu_pt_corr
    mu_pfpho03 = ak.zeros_like(mu_pt_corr)  # placeholders
    mu_pfneu03 = ak.zeros_like(mu_pt_corr)
    mu_pfpui03 = ak.zeros_like(mu_pt_corr)
    mu_besttrkpt = mu_pt_corr
    mu_besttrkpt_err = ak.zeros_like(mu_pt_corr)
    mu_SIP = ak.values_astype(np.abs(mu_sip3d), np.float32)

    # Photons
    ph_pt  = arr.get("Photon_pt", ak.Array([]))
    ph_eta = arr.get("Photon_eta", ak.Array([]))
    ph_phi = arr.get("Photon_phi", ak.Array([]))
    ph_m   = arr.get("Photon_mass", ak.zeros_like(ph_pt))
    ph_E_nom = ak.values_astype(np.sqrt((ph_pt*np.cosh(ph_eta))**2 + ph_m**2), np.float32)
    ph_r9  = arr.get("Photon_r9", ak.zeros_like(ph_pt))
    ph_hoe = arr.get("Photon_hoe", ak.zeros_like(ph_pt))
    ph_sieie = arr.get("Photon_sieie", ak.zeros_like(ph_pt))
    ph_eVeto = arr.get("Photon_electronVeto", ak.zeros_like(ph_pt))
    ph_sieip = ak.values_astype(arr.get("Photon_sieip", ak.zeros_like(ph_pt)), np.float32)
    ph_e2x2  = ak.values_astype(arr.get("Photon_e2x2", ak.zeros_like(ph_pt)), np.float32)
    ph_e5x5  = ak.values_astype(arr.get("Photon_e5x5", ak.zeros_like(ph_pt)), np.float32)

    have_ph_corr = (ph_cset is not None) and (PH_EN_NAME in getattr(ph_cset, "_corrections", {})) and (not args.no_pho_energy_corr)
    def pho_fE(eta, r9, pt, syst):
        return eval_safe(ph_cset, PH_EN_NAME, float(eta), float(r9), float(pt), syst, default=1.0)

    if have_ph_corr:
        def fE_map(syst):
            return ak.Array([[ pho_fE(e,r,pt,syst) for e,r,pt in zip(row_eta,row_r9,row_pt) ]
                              for row_eta,row_r9,row_pt in zip(ph_eta,ph_r9,ph_pt)])
        f_nom      = fE_map("nom")
        f_stat_up  = fE_map("stat_up")
        f_stat_dn  = fE_map("stat_dn")
        f_syst_up  = fE_map("syst_up")
        f_syst_dn  = fE_map("syst_dn")
        f_gain_up  = fE_map("gain_up")
        f_gain_dn  = fE_map("gain_dn")
        f_rho_up   = fE_map("rho_up")
        f_rho_dn   = fE_map("rho_dn")
        f_phi_up   = fE_map("phi_up")
    else:
        ones = ak.ones_like(ph_pt, dtype=np.float32)
        f_nom = f_stat_up = f_stat_dn = f_syst_up = f_syst_dn = f_gain_up = f_gain_dn = f_rho_up = f_rho_dn = f_phi_up = ones

    ph_E_corr   = ph_E_nom * f_nom
    phoCalibEt  = ph_E_corr / np.cosh(ph_eta)
    phoScale_stat_up = ph_E_nom * f_stat_up
    phoScale_stat_dn = ph_E_nom * f_stat_dn
    phoScale_syst_up = ph_E_nom * f_syst_up
    phoScale_syst_dn = ph_E_nom * f_syst_dn
    phoScale_gain_up = ph_E_nom * f_gain_up
    phoScale_gain_dn = ph_E_nom * f_gain_dn
    phoResol_rho_up  = ph_E_nom * f_rho_up
    phoResol_rho_dn  = ph_E_nom * f_rho_dn
    phoResol_phi_up  = ph_E_nom * f_phi_up

    # Jets
    jet_pt  = arr.get("Jet_pt", ak.Array([]))
    jet_eta = arr.get("Jet_eta", ak.Array([]))
    jet_phi = arr.get("Jet_phi", ak.Array([]))
    jet_m   = arr.get("Jet_mass", ak.zeros_like(jet_pt))
    jet_E   = ak.values_astype(np.sqrt((jet_pt*np.cosh(jet_eta))**2 + jet_m**2), np.float32)
    jet_neHEF = arr.get("Jet_neHEF", ak.zeros_like(jet_pt))
    jet_neEmEF= arr.get("Jet_neEmEF", ak.zeros_like(jet_pt))
    jet_chHEF = arr.get("Jet_chHEF", ak.zeros_like(jet_pt))
    jet_chEmEF= arr.get("Jet_chEmEF", ak.zeros_like(jet_pt))
    jet_muEF  = arr.get("Jet_muEF", ak.zeros_like(jet_pt))
    jet_chMult= arr.get("Jet_chMult", ak.zeros_like(jet_pt))
    jet_neMult= arr.get("Jet_neMult", ak.zeros_like(jet_pt))
    jet_id    = arr.get("Jet_jetId", ak.zeros_like(jet_pt))

    have_jet_corr = (jet_cset is not None) and ((JER_SF_NAME in getattr(jet_cset,"_corrections",{})) or (JEC_UNC_NAME in getattr(jet_cset,"_corrections",{})))
    def jer_sf(eta, pt, rho_val, syst):
        return eval_safe(jet_cset, JER_SF_NAME, float(eta), float(pt), float(rho_val), syst, default=1.0)
    def jec_unc_rel(eta, pt):
        return eval_safe(jet_cset, JEC_UNC_NAME, float(eta), float(pt), default=0.0)

    if have_jet_corr:
        rho_ev = rho
        jetP4Smear   = ak.Array([[ jer_sf(e,pt,r,"nom") for e,pt in zip(row_eta,row_pt) ] for row_eta,row_pt,r in zip(jet_eta,jet_pt,rho_ev)])
        jetP4SmearUp = ak.Array([[ jer_sf(e,pt,r,"up")  for e,pt in zip(row_eta,row_pt) ] for row_eta,row_pt,r in zip(jet_eta,jet_pt,rho_ev)])
        jetP4SmearDo = ak.Array([[ jer_sf(e,pt,r,"down")for e,pt in zip(row_eta,row_pt) ] for row_eta,row_pt,r in zip(jet_eta,jet_pt,rho_ev)])
        jec_rel = ak.Array([[ jec_unc_rel(e,pt) for e,pt in zip(row_eta,row_pt) ] for row_eta,row_pt in zip(jet_eta,jet_pt)])
        jetJECUnc = jec_rel * jet_pt  # absolute pT delta (GeV), to match your xAna use
    else:
        jetP4Smear   = ak.ones_like(jet_pt, dtype=np.float32)
        jetP4SmearUp = ak.ones_like(jet_pt, dtype=np.float32)
        jetP4SmearDo = ak.ones_like(jet_pt, dtype=np.float32)
        jetJECUnc    = ak.zeros_like(jet_pt, dtype=np.float32)

    # MC info
    if args.isMC:
        genWeight = arr.get("genWeight", ak.ones_like(event, dtype=np.float32))
        nTrue = arr.get("Pileup_nTrueInt", ak.zeros_like(event, dtype=np.float32))
        puTrue = ak.concatenate([nTrue[:,None], nTrue[:,None]], axis=1)

        gp_pid  = arr.get("GenPart_pdgId", ak.Array([]))
        gp_pt   = arr.get("GenPart_pt", ak.Array([]))
        gp_eta  = arr.get("GenPart_eta", ak.Array([]))
        gp_phi  = arr.get("GenPart_phi", ak.Array([]))
        gp_mass = arr.get("GenPart_mass", ak.zeros_like(gp_pt))
        gp_midx = arr.get("GenPart_genPartIdxMother", ak.zeros_like(gp_pt)-1)

        # mother and grandmother pdgId
        def mom_and_gmom(pid_row, midx_row):
            moms, gmoms = [], []
            pid_list = ak.to_list(pid_row)
            midx_list = ak.to_list(midx_row)
            for j, mi in enumerate(midx_list):
                if mi is None or mi < 0 or mi >= len(pid_list):
                    moms.append(0); gmoms.append(0); continue
                moms.append(pid_list[mi])
                gmi = midx_list[mi] if mi < len(midx_list) else -1
                if gmi is None or gmi < 0 or gmi >= len(pid_list):
                    gmoms.append(0)
                else:
                    gmoms.append(pid_list[gmi])
            return moms, gmoms
        mcMomPID = ak.Array([ mom_and_gmom(pid_row, midx_row)[0] for pid_row, midx_row in zip(gp_pid, gp_midx) ])
        mcGMomPID= ak.Array([ mom_and_gmom(pid_row, midx_row)[1] for pid_row, midx_row in zip(gp_pid, gp_midx) ])

        # LHE
        lhe_pid  = arr.get("LHEPart_pdgId", ak.Array([]))
        lhe_pt   = arr.get("LHEPart_pt", ak.Array([]))
        lhe_eta  = arr.get("LHEPart_eta", ak.Array([]))
        lhe_phi  = arr.get("LHEPart_phi", ak.Array([]))
        lhe_mass = arr.get("LHEPart_mass", ak.zeros_like(lhe_pt))
        lhe_px = lhe_pt * np.cos(lhe_phi)
        lhe_py = lhe_pt * np.sin(lhe_phi)
        lhe_pz = lhe_pt * np.sinh(lhe_eta)
        lhe_E  = np.sqrt(lhe_pt**2 * np.cosh(lhe_eta)**2 + lhe_mass**2)
    else:
        genWeight = ak.ones_like(event, dtype=np.float32)
        puTrue = ak.Array([[0.0,0.0] for _ in range(len(event))])
        gp_pid=gp_pt=gp_eta=gp_phi=gp_mass=mcMomPID=mcGMomPID=ak.Array([])
        lhe_pid=lhe_px=lhe_py=lhe_pz=lhe_E=ak.Array([])

    # -------- Write ROOT miniTree ----------
    fout = ROOT.TFile(args.output, "RECREATE")
    tname = "miniTree" if args.variation == "Nominal" else f"miniTree_{args.variation}"
    tree = ROOT.TTree(tname, tname)

    # Scalars
    rho_f = np.zeros(1, dtype=np.float32)
    rhoAll_f = np.zeros(1, dtype=np.float32)
    event_l = np.zeros(1, dtype=np.int64)
    run_i = np.zeros(1, dtype=np.int32)
    lumis_i = np.zeros(1, dtype=np.int32)
    HLTEleMuX_u = np.zeros(1, dtype=np.uint64)
    isPVGood_b = np.zeros(1, dtype=np.bool_)
    genWeight_f = np.zeros(1, dtype=np.float32)
    # Prefire placeholders (Run 3)
    L1ECALPrefire    = np.ones(1, dtype=np.float64)
    L1ECALPrefireUp  = np.ones(1, dtype=np.float64)
    L1ECALPrefireDown= np.ones(1, dtype=np.float64)
    MuonPrefire      = np.ones(1, dtype=np.float64)
    MuonPrefireUp    = np.ones(1, dtype=np.float64)
    MuonPrefireDown  = np.ones(1, dtype=np.float64)

    tree.Branch("rho", rho_f, "rho/F")
    tree.Branch("rhoAll", rhoAll_f, "rhoAll/F")
    tree.Branch("event", event_l, "event/L")
    tree.Branch("run", run_i, "run/I")
    tree.Branch("lumis", lumis_i, "lumis/I")
    tree.Branch("HLTEleMuX", HLTEleMuX_u, "HLTEleMuX/l")
    tree.Branch("isPVGood", isPVGood_b, "isPVGood/O")
    if args.isMC:
        puTrue_vec = ROOT.std.vector('float')()
        tree.Branch("puTrue", puTrue_vec)
        tree.Branch("genWeight", genWeight_f, "genWeight/F")
        tree.Branch("L1ECALPrefire", L1ECALPrefire, "L1ECALPrefire/D")
        tree.Branch("L1ECALPrefireUp", L1ECALPrefireUp, "L1ECALPrefireUp/D")
        tree.Branch("L1ECALPrefireDown", L1ECALPrefireDown, "L1ECALPrefireDown/D")
        tree.Branch("MuonPrefire", MuonPrefire, "MuonPrefire/D")
        tree.Branch("MuonPrefireUp", MuonPrefireUp, "MuonPrefireUp/D")
        tree.Branch("MuonPrefireDown", MuonPrefireDown, "MuonPrefireDown/D")

    # Helpers to bind std::vector
    def vfloat(name):
        v = ROOT.std.vector('float')(); tree.Branch(name, v); return v
    def vint(name):
        v = ROOT.std.vector('int')(); tree.Branch(name, v); return v
    def vushort(name):
        v = ROOT.std.vector('unsigned short')(); tree.Branch(name, v); return v

    # Muon branches
    nMu_i = np.zeros(1, dtype=np.int32); tree.Branch("nMu", nMu_i, "nMu/I")
    muPt=vfloat("muPt"); muEta=vfloat("muEta"); muPhi=vfloat("muPhi"); muEn=vfloat("muEn")
    muD0=vfloat("muD0"); muDz=vfloat("muDz")
    muBestTrkPtError=vfloat("muBestTrkPtError"); muBestTrkPt=vfloat("muBestTrkPt")
    muSIP=vfloat("muSIP")
    muPFChIso03=vfloat("muPFChIso03"); muPFPhoIso03=vfloat("muPFPhoIso03"); muPFNeuIso03=vfloat("muPFNeuIso03"); muPFPUIso03=vfloat("muPFPUIso03")
    muCharge=vint("muCharge"); muType=vint("muType"); muTrkLayers=vint("muTrkLayers"); muBestTrkType=vint("muBestTrkType")
    muPixelHits=vint("muPixelHits"); muStations=vint("muStations"); muMatches=vint("muMatches")

    # Photon branches
    nPho_i = np.zeros(1, dtype=np.int32); tree.Branch("nPho", nPho_i, "nPho/I")
    phoE=vfloat("phoE"); phoEt=vfloat("phoEt"); phoCalibEt_v=vfloat("phoCalibEt"); phoEta=vfloat("phoEta"); phoPhi=vfloat("phoPhi")
    phoSCEta=vfloat("phoSCEta"); phoSCPhi=vfloat("phoSCPhi"); phoIDMVA=vfloat("phoIDMVA"); phoEleVeto=vint("phoEleVeto")
    phoSCRawE=vfloat("phoSCRawE"); phoSigmaIEtaIEtaFull5x5=vfloat("phoSigmaIEtaIEtaFull5x5")
    phoSCEtaWidth=vfloat("phoSCEtaWidth"); phoSCPhiWidth=vfloat("phoSCPhiWidth"); phoSigmaIEtaIPhiFull5x5=vfloat("phoSigmaIEtaIPhiFull5x5")
    phoPFPhoIso=vfloat("phoPFPhoIso"); phoPFChIso=vfloat("phoPFChIso"); phoPFChWorstIso=vfloat("phoPFChWorstIso")
    phoE2x2Full5x5=vfloat("phoE2x2Full5x5"); phoE5x5Full5x5=vfloat("phoE5x5Full5x5")
    phoESEffSigmaRR=vfloat("phoESEffSigmaRR"); phoESEnP1=vfloat("phoESEnP1"); phoESEnP2=vfloat("phoESEnP2")
    phoTrkIsoHollowConeDR03=vfloat("phoTrkIsoHollowConeDR03"); phoHoverE=vfloat("phoHoverE")
    phoScale_stat_up=vfloat("phoScale_stat_up"); phoScale_syst_up=vfloat("phoScale_syst_up"); phoScale_gain_up=vfloat("phoScale_gain_up")
    phoScale_stat_dn=vfloat("phoScale_stat_dn"); phoScale_syst_dn=vfloat("phoScale_syst_dn"); phoScale_gain_dn=vfloat("phoScale_gain_dn")
    phoResol_phi_up=vfloat("phoResol_phi_up"); phoResol_rho_up=vfloat("phoResol_rho_up"); phoResol_rho_dn=vfloat("phoResol_rho_dn")
    phoCorrR9Full5x5=vfloat("phoCorrR9Full5x5"); phoCorrHggIDMVA=vfloat("phoCorrHggIDMVA"); phoR9Full5x5=vfloat("phoR9Full5x5")

    # Jets
    nJet_i = np.zeros(1, dtype=np.int32); tree.Branch("nJet", nJet_i, "nJet/I")
    jetPt=vfloat("jetPt"); jetEta=vfloat("jetEta"); jetPhi=vfloat("jetPhi"); jetEn=vfloat("jetEn")
    jetNHF=vfloat("jetNHF"); jetNEF=vfloat("jetNEF"); jetID=vfloat("jetID"); jetCHF=vfloat("jetCHF"); jetCEF=vfloat("jetCEF"); jetMUF=vfloat("jetMUF")
    jetNCH=vint("jetNCH"); jetNNP=vint("jetNNP")
    if args.isMC:
        jetP4Smear_v=vfloat("jetP4Smear"); jetP4SmearUp_v=vfloat("jetP4SmearUp"); jetP4SmearDo_v=vfloat("jetP4SmearDo"); jetJECUnc_v=vfloat("jetJECUnc")

    # MC gen/LHE
    if args.isMC:
        nMC_i = np.zeros(1, dtype=np.int32); tree.Branch("nMC", nMC_i, "nMC/I")
        mcPID=vint("mcPID"); mcMomPID=vint("mcMomPID"); mcGMomPID=vint("mcGMomPID")
        mcPt=vfloat("mcPt"); mcEta=vfloat("mcEta"); mcPhi=vfloat("mcPhi"); mcMass=vfloat("mcMass")
        mcStatusFlag=vushort("mcStatusFlag")
        nLHE_i = np.zeros(1, dtype=np.int32); tree.Branch("nLHE", nLHE_i, "nLHE/I")
        lheE=vfloat("lheE"); lhePx=vfloat("lhePx"); lhePy=vfloat("lhePy"); lhePz=vfloat("lhePz"); lhePID=vint("lhePID")

    # Event loop
    nev = len(event)
    for ie in range(nev):
        # Scalars
        run_i[0]   = int(run[ie])
        lumis_i[0] = int(lumi[ie])
        event_l[0] = int(event[ie])
        rho_f[0]   = float(rho[ie])
        rhoAll_f[0]= float(rhoAll[ie])
        HLTEleMuX_u[0] = int(HLTEleMuX[ie])
        isPVGood_b[0]  = bool(isPVGood[ie])
        if args.isMC:
            genWeight_f[0] = float(genWeight[ie])
            # puTrue
            puTrue_vec.clear()
            for val in ak.to_list(puTrue[ie]):
                puTrue_vec.push_back(float(val))

        # Clear vectors
        for v in [muPt,muEta,muPhi,muEn,muD0,muDz,muBestTrkPtError,muBestTrkPt,muSIP,muPFChIso03,muPFPhoIso03,muPFNeuIso03,muPFPUIso03,muCharge,muType,muTrkLayers,muBestTrkType,muPixelHits,muStations,muMatches,
                  phoE,phoEt,phoCalibEt_v,phoEta,phoPhi,phoSCEta,phoSCPhi,phoIDMVA,phoEleVeto,phoSCRawE,phoSigmaIEtaIEtaFull5x5,phoSCEtaWidth,phoSCPhiWidth,phoSigmaIEtaIPhiFull5x5,
                  phoPFPhoIso,phoPFChIso,phoPFChWorstIso,phoE2x2Full5x5,phoE5x5Full5x5,phoESEffSigmaRR,phoESEnP1,phoESEnP2,phoTrkIsoHollowConeDR03,phoHoverE,
                  phoScale_stat_up,phoScale_syst_up,phoScale_gain_up,phoScale_stat_dn,phoScale_syst_dn,phoScale_gain_dn,phoResol_phi_up,phoResol_rho_up,phoResol_rho_dn,
                  phoCorrR9Full5x5,phoCorrHggIDMVA,phoR9Full5x5,
                  jetPt,jetEta,jetPhi,jetEn,jetNHF,jetNEF,jetID,jetCHF,jetCEF,jetMUF,jetNCH,jetNNP]:
            v.clear()
        if args.isMC:
            for v in [] if not args.isMC else [jetP4Smear_v,jetP4SmearUp_v,jetP4SmearDo_v,jetJECUnc_v,
                                               mcPID,mcMomPID,mcGMomPID,mcPt,mcEta,mcPhi,mcMass,mcStatusFlag,
                                               lheE,lhePx,lhePy,lhePz,lhePID]:
                v.clear()

        # Muons
        if len(mu_pt) > ie:
            for j in range(len(mu_pt[ie])):
                muPt.push_back(float(mu_pt_corr[ie][j]))
                muEta.push_back(float(mu_eta[ie][j]))
                muPhi.push_back(float(mu_phi[ie][j]))
                muEn.push_back(float(mu_en_corr[ie][j]))
                muD0.push_back(float(mu_dxy[ie][j]))
                muDz.push_back(float(mu_dz[ie][j]))
                muBestTrkPt.push_back(float(mu_besttrkpt[ie][j]))
                muBestTrkPtError.push_back(0.0)
                muSIP.push_back(float(mu_SIP[ie][j]))
                muPFChIso03.push_back(float(mu_pfchiso03[ie][j]))
                muPFPhoIso03.push_back(0.0)
                muPFNeuIso03.push_back(0.0)
                muPFPUIso03.push_back(0.0)
                muCharge.push_back(int(mu_q[ie][j]))
                muType.push_back(int(mu_type_bits[ie][j]))
                muTrkLayers.push_back(int(mu_nLay[ie][j]))
                muBestTrkType.push_back(1)  # placeholder
                muPixelHits.push_back(int(mu_nPix[ie][j]))
                muStations.push_back(int(mu_nSta[ie][j]))
                muMatches.push_back(int(mu_nMat[ie][j]))
        nMu_i[0] = muPt.size()

        # Photons
        if len(ph_pt) > ie:
            for j in range(len(ph_pt[ie])):
                E_nom = float(ph_E_nom[ie][j])
                eta   = float(ph_eta[ie][j])
                phi   = float(ph_phi[ie][j])
                phoE.push_back(E_nom)
                phoEt.push_back(float(ph_pt[ie][j]))
                phoCalibEt_v.push_back(float(phoCalibEt[ie][j]))
                phoEta.push_back(eta)
                phoPhi.push_back(phi)
                phoSCEta.push_back(eta)   # SC η/φ not in Nano by default
                phoSCPhi.push_back(phi)
                phoIDMVA.push_back(-99.0) # placeholder
                phoEleVeto.push_back(int(ph_eVeto[ie][j]))
                phoSCRawE.push_back(E_nom) # proxy
                phoSigmaIEtaIEtaFull5x5.push_back(float(ph_sieie[ie][j]))
                phoSCEtaWidth.push_back(0.0)
                phoSCPhiWidth.push_back(0.0)
                phoSigmaIEtaIPhiFull5x5.push_back(float(ph_sieip[ie][j]) if len(ph_sieip)>ie and len(ph_sieip[ie])>j else 0.0)
                phoPFPhoIso.push_back(0.0)
                phoPFChIso.push_back(0.0)
                phoPFChWorstIso.push_back(0.0)
                phoE2x2Full5x5.push_back(float(ph_e2x2[ie][j]) if len(ph_e2x2)>ie and len(ph_e2x2[ie])>j else 0.0)
                phoE5x5Full5x5.push_back(float(ph_e5x5[ie][j]) if len(ph_e5x5)>ie and len(ph_e5x5[ie])>j else 0.0)
                phoESEffSigmaRR.push_back(0.0)
                phoESEnP1.push_back(0.0)
                phoESEnP2.push_back(0.0)
                phoTrkIsoHollowConeDR03.push_back(0.0)
                phoHoverE.push_back(float(ph_hoe[ie][j]))
                # variations (energies)
                phoScale_stat_up.push_back(float(phoScale_stat_up[ie][j]))
                phoScale_stat_dn.push_back(float(phoScale_stat_dn[ie][j]))
                phoScale_syst_up.push_back(float(phoScale_syst_up[ie][j]))
                phoScale_syst_dn.push_back(float(phoScale_syst_dn[ie][j]))
                phoScale_gain_up.push_back(float(phoScale_gain_up[ie][j]))
                phoScale_gain_dn.push_back(float(phoScale_gain_dn[ie][j]))
                phoResol_rho_up.push_back(float(phoResol_rho_up[ie][j]))
                phoResol_rho_dn.push_back(float(phoResol_rho_dn[ie][j]))
                phoResol_phi_up.push_back(float(phoResol_phi_up[ie][j]))
                # R9
                r9 = float(ph_r9[ie][j])
                phoCorrR9Full5x5.push_back(r9)
                phoR9Full5x5.push_back(r9)
                phoCorrHggIDMVA.push_back(-99.0)
        nPho_i[0] = phoEt.size()

        # Jets
        if len(jet_pt) > ie:
            for j in range(len(jet_pt[ie])):
                jetPt.push_back(float(jet_pt[ie][j]))
                jetEta.push_back(float(jet_eta[ie][j]))
                jetPhi.push_back(float(jet_phi[ie][j]))
                jetEn.push_back(float(jet_E[ie][j]))
                jetNHF.push_back(float(jet_neHEF[ie][j]))
                jetNEF.push_back(float(jet_neEmEF[ie][j]))
                jetCHF.push_back(float(jet_chHEF[ie][j]))
                jetCEF.push_back(float(jet_chEmEF[ie][j]))
                jetMUF.push_back(float(jet_muEF[ie][j]))
                jetNCH.push_back(int(jet_chMult[ie][j]))
                jetNNP.push_back(int(jet_neMult[ie][j]))
                jetID.push_back(1.0 if int(jet_id[ie][j]) >= 4 else 0.0)  # UL tightLepVeto≈4
                if args.isMC:
                    jetP4Smear_v.push_back(float(jetP4Smear[ie][j]))
                    jetP4SmearUp_v.push_back(float(jetP4SmearUp[ie][j]))
                    jetP4SmearDo_v.push_back(float(jetP4SmearDo[ie][j]))
                    jetJECUnc_v.push_back(float(jetJECUnc[ie][j]))
        nJet_i[0] = jetPt.size()

        # MC gen and LHE
        if args.isMC:
            if len(gp_pid) > ie:
                for j in range(len(gp_pid[ie])):
                    mcPID.push_back(int(gp_pid[ie][j]))
                    mcMomPID.push_back(int(mcMomPID[ie][j]) if len(mcMomPID)>ie and len(mcMomPID[ie])>j else 0)
                    mcGMomPID.push_back(int(mcGMomPID[ie][j]) if len(mcGMomPID)>ie and len(mcGMomPID[ie])>j else 0)
                    mcPt.push_back(float(gp_pt[ie][j]))
                    mcEta.push_back(float(gp_eta[ie][j]))
                    mcPhi.push_back(float(gp_phi[ie][j]))
                    mcMass.push_back(float(gp_mass[ie][j]))
                    mcStatusFlag.push_back(0)
            nMC_i[0] = mcPID.size()

            if len(lhe_pid) > ie:
                for j in range(len(lhe_pid[ie])):
                    lhePID.push_back(int(lhe_pid[ie][j]))
                    lhePx.push_back(float(lhe_px[ie][j]))
                    lhePy.push_back(float(lhe_py[ie][j]))
                    lhePz.push_back(float(lhe_pz[ie][j]))
                    lheE.push_back(float(lhe_E[ie][j]))
            nLHE_i[0] = lhePID.size()

        # Fill this event
        tree.Fill()

    # Write and close
    fout.cd()
    tree.Write()
    fout.Close()

if __name__ == "__main__":
    main()
