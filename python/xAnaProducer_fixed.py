import ROOT
import os
import array
import math
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


# ── Branch helpers ────────────────────────────────────────────────────────────

def _vec(tree, name, ctype="float"):
    v = ROOT.std.vector(ctype)()
    tree.Branch(name, v)
    return v

def _scalar(tree, name, typecode, leaftype):
    arr = array.array(typecode, [0])
    tree.Branch(name, arr, f"{name}/{leaftype}")
    return arr


class xAnaProducer(Module):

    def __init__(self, isMC=True, outDir="."):
        self.isMC = isMC
        self._outDir = outDir
        self.triggerWarningPrinted = False

    # ── beginFile: create our own TTree from scratch ──────────────────────────

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        # noOut=True means outputFile is None — open our own output file.
        inName   = inputFile.GetName()
        baseName = os.path.splitext(os.path.basename(inName))[0]
        self._outPath = os.path.join(self._outDir, baseName + "_xAna.root")
        self._outFile = ROOT.TFile(self._outPath, "RECREATE")
        self._tree = ROOT.TTree("Events", "Events")   # own TTree, no NanoAOD pass-through

        t = self._tree

        # Event scalars
        self._run      = _scalar(t, "run",      'I', 'i')   # UInt_t
        self._lumis    = _scalar(t, "lumis",    'i', 'I')   # Int_t
        self._event    = _scalar(t, "event",    'L', 'l')   # ULong64_t
        self._rho      = _scalar(t, "rho",      'f', 'F')
        self._rhoAll   = _scalar(t, "rhoAll",   'f', 'F')
        self._isPVGood = _scalar(t, "isPVGood", 'b', 'O')
        self._HLTEleMuX= _scalar(t, "HLTEleMuX",'L', 'l')

        if self.isMC:
            self._puTrue            = _vec   (t, "puTrue")
            self._genWeight         = _scalar(t, "genWeight",         'f', 'F')
            self._L1ECALPrefire     = _scalar(t, "L1ECALPrefire",     'd', 'D')
            self._L1ECALPrefireUp   = _scalar(t, "L1ECALPrefireUp",   'd', 'D')
            self._L1ECALPrefireDown = _scalar(t, "L1ECALPrefireDown", 'd', 'D')
            self._MuonPrefire       = _scalar(t, "MuonPrefire",       'd', 'D')
            self._MuonPrefireUp     = _scalar(t, "MuonPrefireUp",     'd', 'D')
            self._MuonPrefireDown   = _scalar(t, "MuonPrefireDown",   'd', 'D')

        # Muons
        self._nMu             = _scalar(t, "nMu",             'i', 'I')
        self._muPt            = _vec   (t, "muPt")
        self._muEta           = _vec   (t, "muEta")
        self._muPhi           = _vec   (t, "muPhi")
        self._muEn            = _vec   (t, "muEn")
        self._muD0            = _vec   (t, "muD0")
        self._muDz            = _vec   (t, "muDz")
        self._muBestTrkPt     = _vec   (t, "muBestTrkPt")
        self._muBestTrkPtError= _vec   (t, "muBestTrkPtError")
        self._muSIP           = _vec   (t, "muSIP")
        self._muPFChIso03     = _vec   (t, "muPFChIso03")
        self._muPFPhoIso03    = _vec   (t, "muPFPhoIso03")
        self._muPFNeuIso03    = _vec   (t, "muPFNeuIso03")
        self._muPFPUIso03     = _vec   (t, "muPFPUIso03")
        self._muCharge        = _vec   (t, "muCharge",    "int")
        self._muType          = _vec   (t, "muType",      "int")
        self._muTrkLayers     = _vec   (t, "muTrkLayers", "int")
        self._muBestTrkType   = _vec   (t, "muBestTrkType","int")
        self._muPixelHits     = _vec   (t, "muPixelHits", "int")
        self._muStations      = _vec   (t, "muStations",  "int")
        self._muMatches       = _vec   (t, "muMatches",   "int")

        # Photons
        self._nPho                    = _scalar(t, "nPho", 'i', 'I')
        self._phoE                    = _vec(t, "phoE")
        self._phoEt                   = _vec(t, "phoEt")
        self._phoCalibEt              = _vec(t, "phoCalibEt")
        self._phoEta                  = _vec(t, "phoEta")
        self._phoPhi                  = _vec(t, "phoPhi")
        self._phoSCEta                = _vec(t, "phoSCEta")
        self._phoSCPhi                = _vec(t, "phoSCPhi")
        self._phoIDMVA                = _vec(t, "phoIDMVA")
        self._phoSCRawE               = _vec(t, "phoSCRawE")
        self._phoSigmaIEtaIEtaFull5x5 = _vec(t, "phoSigmaIEtaIEtaFull5x5")
        self._phoSCEtaWidth           = _vec(t, "phoSCEtaWidth")
        self._phoSCPhiWidth           = _vec(t, "phoSCPhiWidth")
        self._phoSigmaIEtaIPhiFull5x5 = _vec(t, "phoSigmaIEtaIPhiFull5x5")
        self._phoPFPhoIso             = _vec(t, "phoPFPhoIso")
        self._phoPFChIso              = _vec(t, "phoPFChIso")
        self._phoPFChWorstIso         = _vec(t, "phoPFChWorstIso")
        self._phoS4Full5x5            = _vec(t, "phoS4Full5x5")
        self._phoE2x2Full5x5          = _vec(t, "phoE2x2Full5x5")   # = s4 * E5x5
        self._phoE5x5Full5x5          = _vec(t, "phoE5x5Full5x5")
        self._phoESEffSigmaRR         = _vec(t, "phoESEffSigmaRR")
        self._phoESEnP1               = _vec(t, "phoESEnP1")
        self._phoESEnP2               = _vec(t, "phoESEnP2")
        self._phoTrkIsoHollowConeDR03 = _vec(t, "phoTrkIsoHollowConeDR03")
        self._phoHoverE               = _vec(t, "phoHoverE")
        self._phoScale_stat_up        = _vec(t, "phoScale_stat_up")
        self._phoScale_syst_up        = _vec(t, "phoScale_syst_up")
        self._phoScale_gain_up        = _vec(t, "phoScale_gain_up")
        self._phoScale_stat_dn        = _vec(t, "phoScale_stat_dn")
        self._phoScale_syst_dn        = _vec(t, "phoScale_syst_dn")
        self._phoScale_gain_dn        = _vec(t, "phoScale_gain_dn")
        self._phoResol_phi_up         = _vec(t, "phoResol_phi_up")
        self._phoResol_rho_up         = _vec(t, "phoResol_rho_up")
        self._phoResol_rho_dn         = _vec(t, "phoResol_rho_dn")
        self._phoCorrR9Full5x5        = _vec(t, "phoCorrR9Full5x5")
        self._phoCorrHggIDMVA         = _vec(t, "phoCorrHggIDMVA")
        self._phoR9Full5x5            = _vec(t, "phoR9Full5x5")
        self._phoEleVeto              = _vec(t, "phoEleVeto", "int")

        # Jets
        self._nJet    = _scalar(t, "nJet", 'i', 'I')
        self._jetPt   = _vec(t, "jetPt")
        self._jetEta  = _vec(t, "jetEta")
        self._jetPhi  = _vec(t, "jetPhi")
        self._jetEn   = _vec(t, "jetEn")
        self._jetNHF  = _vec(t, "jetNHF")
        self._jetNEF  = _vec(t, "jetNEF")
        self._jetID   = _vec(t, "jetID")       # vector<float> in xAna.C
        self._jetCHF  = _vec(t, "jetCHF")
        self._jetCEF  = _vec(t, "jetCEF")
        self._jetMUF  = _vec(t, "jetMUF")
        self._jetNCH  = _vec(t, "jetNCH", "int")
        self._jetNNP  = _vec(t, "jetNNP", "int")

        if self.isMC:
            self._jetP4Smear   = _vec(t, "jetP4Smear")
            self._jetP4SmearUp = _vec(t, "jetP4SmearUp")
            self._jetP4SmearDo = _vec(t, "jetP4SmearDo")
            self._jetJECUnc    = _vec(t, "jetJECUnc")

        # Generator / LHE (MC only)
        if self.isMC:
            self._nMC          = _scalar(t, "nMC",  'i', 'I')
            self._nLHE         = _scalar(t, "nLHE", 'i', 'I')
            self._mcPID        = _vec(t, "mcPID",       "int")
            self._mcMomPID     = _vec(t, "mcMomPID",    "int")
            self._mcGMomPID    = _vec(t, "mcGMomPID",   "int")
            self._mcPt         = _vec(t, "mcPt")
            self._mcEta        = _vec(t, "mcEta")
            self._mcPhi        = _vec(t, "mcPhi")
            self._mcMass       = _vec(t, "mcMass")
            self._mcStatusFlag = _vec(t, "mcStatusFlag", "unsigned short")
            self._lhePID       = _vec(t, "lhePID", "int")
            self._lheE         = _vec(t, "lheE")
            self._lhePx        = _vec(t, "lhePx")
            self._lhePy        = _vec(t, "lhePy")
            self._lhePz        = _vec(t, "lhePz")

    # ── endFile: write our TTree to the output file ───────────────────────────

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self._outFile.cd()
        self._tree.Write()
        self._outFile.Close()
        print(f"[DONE] Written: {self._outPath}")

    # ── clear per-event vectors ───────────────────────────────────────────────

    def _clear_vecs(self):
        float_vecs = [
            self._muPt, self._muEta, self._muPhi, self._muEn,
            self._muD0, self._muDz, self._muBestTrkPt, self._muBestTrkPtError,
            self._muSIP, self._muPFChIso03, self._muPFPhoIso03,
            self._muPFNeuIso03, self._muPFPUIso03,
            self._phoE, self._phoEt, self._phoCalibEt, self._phoEta, self._phoPhi,
            self._phoSCEta, self._phoSCPhi, self._phoIDMVA, self._phoSCRawE,
            self._phoSigmaIEtaIEtaFull5x5, self._phoSCEtaWidth, self._phoSCPhiWidth,
            self._phoSigmaIEtaIPhiFull5x5, self._phoPFPhoIso, self._phoPFChIso,
            self._phoPFChWorstIso, self._phoS4Full5x5, self._phoE2x2Full5x5,
            self._phoE5x5Full5x5, self._phoESEffSigmaRR, self._phoESEnP1, self._phoESEnP2,
            self._phoTrkIsoHollowConeDR03, self._phoHoverE,
            self._phoScale_stat_up, self._phoScale_syst_up, self._phoScale_gain_up,
            self._phoScale_stat_dn, self._phoScale_syst_dn, self._phoScale_gain_dn,
            self._phoResol_phi_up, self._phoResol_rho_up, self._phoResol_rho_dn,
            self._phoCorrR9Full5x5, self._phoCorrHggIDMVA, self._phoR9Full5x5,
            self._jetPt, self._jetEta, self._jetPhi, self._jetEn,
            self._jetNHF, self._jetNEF, self._jetID, self._jetCHF,
            self._jetCEF, self._jetMUF,
        ]
        int_vecs = [
            self._muCharge, self._muType, self._muTrkLayers, self._muBestTrkType,
            self._muPixelHits, self._muStations, self._muMatches,
            self._phoEleVeto, self._jetNCH, self._jetNNP,
        ]
        for v in float_vecs + int_vecs:
            v.clear()

        if self.isMC:
            for v in [
                self._puTrue,
                self._jetP4Smear, self._jetP4SmearUp, self._jetP4SmearDo, self._jetJECUnc,
                self._mcPID, self._mcMomPID, self._mcGMomPID,
                self._mcPt, self._mcEta, self._mcPhi, self._mcMass, self._mcStatusFlag,
                self._lhePID, self._lheE, self._lhePx, self._lhePy, self._lhePz,
            ]:
                v.clear()

    # ── analyze ───────────────────────────────────────────────────────────────

    def analyze(self, event):

        # Primary vertex
        if getattr(event, "PV_npvsGood", 0) < 1:
            return False

        # ── Triggers ─────────────────────────────────────────────────────────
        mu17pho, isomu = False, False
        usedMu17Pho, usedIsoMu = None, None

        for name in ["HLT_Mu17_Photon30_IsoCaloId", "HLT_Mu17_Photon30",
                     "HLT_Mu17_Photon30_CaloId", "HLT_Mu17_Photon30_CaloIdIso"]:
            try:
                mu17pho = bool(getattr(event, name)); usedMu17Pho = name; break
            except RuntimeError:
                pass

        for name in ["HLT_IsoMu27", "HLT_IsoMu24", "HLT_Mu27"]:
            try:
                isomu = bool(getattr(event, name)); usedIsoMu = name; break
            except RuntimeError:
                pass

        if not self.triggerWarningPrinted:
            if usedMu17Pho:
                print(f"\033[92m[INFO] Using Mu17+Photon trigger: {usedMu17Pho}\033[0m")
            elif usedIsoMu:
                print(f"\033[93m[WARN] No Mu17+Photon trigger found. Falling back to: {usedIsoMu}\033[0m")
            else:
                print("\033[91m[ERROR] No trigger branches found.\033[0m")
            self.triggerWarningPrinted = True

        if not (mu17pho or isomu):
            return False

        HLTEleMuX = (int(mu17pho) << 8) | (int(isomu) << 19)

        # ── Muons ─────────────────────────────────────────────────────────────
        nMuon = getattr(event, "nMuon", 0)
        muons = []
        for i in range(nMuon):
            pt  = float(event.Muon_pt[i])
            eta = float(event.Muon_eta[i])
            phi = float(event.Muon_phi[i])
            if pt < 5 or abs(eta) > 2.4:
                continue
            m  = float(getattr(event, "Muon_mass", [0.1057]*nMuon)[i])
            en = math.sqrt((pt*math.cosh(eta))**2 + m**2)

            d0  = float(getattr(event, "Muon_dxy",   [0.0]*nMuon)[i])
            dz  = float(getattr(event, "Muon_dz",    [0.0]*nMuon)[i])
            sip = abs(float(getattr(event, "Muon_sip3d", [0.0]*nMuon)[i]))

            rel_chg = getattr(event, "Muon_pfRelIso03_chg", None)
            pfchiso = rel_chg[i]*pt if rel_chg is not None else 0.0

            itype = 0
            if getattr(event, "Muon_isGlobal",  [False]*nMuon)[i]: itype |= (1<<1)
            if getattr(event, "Muon_isTracker", [False]*nMuon)[i]: itype |= (1<<2)
            if getattr(event, "Muon_isPFcand",  [False]*nMuon)[i]: itype |= (1<<5)

            def _int(val): return ord(val) if isinstance(val, str) else int(val)
            trkLayers = _int(getattr(event, "Muon_nTrackerLayers", [0]*nMuon)[i])
            stations  = _int(getattr(event, "Muon_nStations",      [0]*nMuon)[i])
            try:    matches   = _int(event.Muon_nMatches[i])
            except: matches   = 0
            try:    pixelHits = _int(event.Muon_nPixelHits[i])
            except: pixelHits = 0

            muons.append((pt, eta, phi, en, d0, dz, pt, 0.0, sip,
                          pfchiso, 0.0, 0.0, 0.0,
                          int(event.Muon_charge[i]), itype, trkLayers, 1,
                          pixelHits, stations, matches))

        if len(muons) < 2:
            return False

        # ── Photons ───────────────────────────────────────────────────────────
        nPhoIn = getattr(event, "nPhoton", 0)
        photons = []
        for i in range(nPhoIn):
            pt  = float(event.Photon_pt[i])
            eta = float(event.Photon_eta[i])
            phi = float(event.Photon_phi[i])
            if pt < 10 or abs(eta) > 2.5:
                continue
            E = pt * math.cosh(eta)

            sieie = float(getattr(event, "Photon_sieie", [0.0]*nPhoIn)[i])
            sieip = float(getattr(event, "Photon_sieip", [0.0]*nPhoIn)[i])
            hoe   = float(getattr(event, "Photon_hoe",   [0.0]*nPhoIn)[i])
            r9    = float(getattr(event, "Photon_r9",    [0.0]*nPhoIn)[i])
            s4    = float(getattr(event, "Photon_s4",    [0.0]*nPhoIn)[i])
            mvaID = float(getattr(event, "Photon_mvaID", [-99.0]*nPhoIn)[i])
            elVeto= int  (getattr(event, "Photon_electronVeto", [0]*nPhoIn)[i])

            # E2x2 = s4 * E5x5. NanoAOD gives s4=E2x2/E5x5; we set E5x5=1 placeholder.
            e5x5 = 1.0
            e2x2 = s4

            photons.append((E, pt, pt, eta, phi, eta, phi, mvaID,
                            E, sieie, 0.0, 0.0, sieip,
                            0.0, 0.0, 0.0,
                            s4, e2x2, e5x5,
                            0.0, 0.0, 0.0, 0.0, hoe,
                            E, E, E, E, E, E, E, E, E,
                            r9, -99.0, r9, elVeto))

        if len(photons) < 1:
            return False

        # ── Jets ──────────────────────────────────────────────────────────────
        nJetIn = getattr(event, "nJet", 0)
        jets = []
        for i in range(nJetIn):
            pt  = float(event.Jet_pt[i])
            eta = float(event.Jet_eta[i])
            phi = float(event.Jet_phi[i])
            if pt < 20:
                continue
            m  = float(getattr(event, "Jet_mass", [0.0]*nJetIn)[i])
            E  = math.sqrt((pt*math.cosh(eta))**2 + m**2)

            nhf = float(getattr(event, "Jet_neHEF",  [0.0]*nJetIn)[i])
            nef = float(getattr(event, "Jet_neEmEF", [0.0]*nJetIn)[i])
            chf = float(getattr(event, "Jet_chHEF",  [0.0]*nJetIn)[i])
            cef = float(getattr(event, "Jet_chEmEF", [0.0]*nJetIn)[i])
            muf = float(getattr(event, "Jet_muEF",   [0.0]*nJetIn)[i])

            def _int(v): return ord(v) if isinstance(v, str) else int(v)
            nch = _int(getattr(event, "Jet_chMultiplicity", [0]*nJetIn)[i])
            nnp = _int(getattr(event, "Jet_neMultiplicity", [0]*nJetIn)[i])

            jets.append((pt, eta, phi, E, nhf, nef, 1.0, chf, cef, muf, nch, nnp))

        # ── Fill branches ─────────────────────────────────────────────────────
        self._clear_vecs()

        self._run[0]       = int(event.run)
        self._lumis[0]     = int(event.luminosityBlock)
        self._event[0]     = int(event.event)
        rho                = float(getattr(event, "Rho_fixedGridRhoFastjetAll", 0.0))
        self._rho[0]       = rho
        self._rhoAll[0]    = rho
        self._isPVGood[0]  = 1
        self._HLTEleMuX[0] = HLTEleMuX

        if self.isMC:
            self._genWeight[0]         = float(getattr(event, "genWeight", 1.0))
            nTrue                      = float(getattr(event, "Pileup_nTrueInt", 0.0))
            self._puTrue.push_back(nTrue); self._puTrue.push_back(nTrue)
            self._L1ECALPrefire[0]     = 1.0; self._L1ECALPrefireUp[0]   = 1.0
            self._L1ECALPrefireDown[0] = 1.0; self._MuonPrefire[0]       = 1.0
            self._MuonPrefireUp[0]     = 1.0; self._MuonPrefireDown[0]   = 1.0

        self._nMu[0] = len(muons)
        for (pt,eta,phi,en,d0,dz,btkpt,btkpterr,sip,
             pfch,pfpho,pfneu,pfpu,
             ch,typ,trkl,btktyp,pxhit,sta,mat) in muons:
            self._muPt.push_back(pt);    self._muEta.push_back(eta)
            self._muPhi.push_back(phi);  self._muEn.push_back(en)
            self._muD0.push_back(d0);    self._muDz.push_back(dz)
            self._muBestTrkPt.push_back(btkpt); self._muBestTrkPtError.push_back(btkpterr)
            self._muSIP.push_back(sip)
            self._muPFChIso03.push_back(pfch);  self._muPFPhoIso03.push_back(pfpho)
            self._muPFNeuIso03.push_back(pfneu);self._muPFPUIso03.push_back(pfpu)
            self._muCharge.push_back(ch);       self._muType.push_back(typ)
            self._muTrkLayers.push_back(trkl);  self._muBestTrkType.push_back(btktyp)
            self._muPixelHits.push_back(pxhit); self._muStations.push_back(sta)
            self._muMatches.push_back(mat)

        self._nPho[0] = len(photons)
        for (E,et,calet,eta,phi,sceta,scphi,mva,
             scrawE,sieie,etaW,phiW,sieip,
             pfpho,pfch,pfchw,s4,e2x2,e5x5,
             eseff,esp1,esp2,trkiso,hoe,
             sc_su,sy_su,sg_su,sc_sd,sy_sd,sg_sd,
             rph_u,rrh_u,rrh_d,corrR9,corrMVA,R9,elVeto) in photons:
            self._phoE.push_back(E);           self._phoEt.push_back(et)
            self._phoCalibEt.push_back(calet); self._phoEta.push_back(eta)
            self._phoPhi.push_back(phi);       self._phoSCEta.push_back(sceta)
            self._phoSCPhi.push_back(scphi);   self._phoIDMVA.push_back(mva)
            self._phoSCRawE.push_back(scrawE)
            self._phoSigmaIEtaIEtaFull5x5.push_back(sieie)
            self._phoSCEtaWidth.push_back(etaW); self._phoSCPhiWidth.push_back(phiW)
            self._phoSigmaIEtaIPhiFull5x5.push_back(sieip)
            self._phoPFPhoIso.push_back(pfpho); self._phoPFChIso.push_back(pfch)
            self._phoPFChWorstIso.push_back(pfchw)
            self._phoS4Full5x5.push_back(s4);  self._phoE2x2Full5x5.push_back(e2x2)
            self._phoE5x5Full5x5.push_back(e5x5)
            self._phoESEffSigmaRR.push_back(eseff)
            self._phoESEnP1.push_back(esp1);   self._phoESEnP2.push_back(esp2)
            self._phoTrkIsoHollowConeDR03.push_back(trkiso)
            self._phoHoverE.push_back(hoe)
            self._phoScale_stat_up.push_back(sc_su); self._phoScale_syst_up.push_back(sy_su)
            self._phoScale_gain_up.push_back(sg_su); self._phoScale_stat_dn.push_back(sc_sd)
            self._phoScale_syst_dn.push_back(sy_sd); self._phoScale_gain_dn.push_back(sg_sd)
            self._phoResol_phi_up.push_back(rph_u);  self._phoResol_rho_up.push_back(rrh_u)
            self._phoResol_rho_dn.push_back(rrh_d)
            self._phoCorrR9Full5x5.push_back(corrR9); self._phoCorrHggIDMVA.push_back(corrMVA)
            self._phoR9Full5x5.push_back(R9);         self._phoEleVeto.push_back(elVeto)

        self._nJet[0] = len(jets)
        for (pt,eta,phi,en,nhf,nef,jid,chf,cef,muf,nch,nnp) in jets:
            self._jetPt.push_back(pt);   self._jetEta.push_back(eta)
            self._jetPhi.push_back(phi); self._jetEn.push_back(en)
            self._jetNHF.push_back(nhf); self._jetNEF.push_back(nef)
            self._jetID.push_back(jid);  self._jetCHF.push_back(chf)
            self._jetCEF.push_back(cef); self._jetMUF.push_back(muf)
            self._jetNCH.push_back(nch); self._jetNNP.push_back(nnp)
            if self.isMC:
                self._jetP4Smear.push_back(1.0);   self._jetP4SmearUp.push_back(1.0)
                self._jetP4SmearDo.push_back(1.0); self._jetJECUnc.push_back(0.0)

        if self.isMC:
            nGen = getattr(event, "nGenPart", 0)
            self._nMC[0] = nGen
            for i in range(nGen):
                self._mcPID.push_back    (int  (event.GenPart_pdgId[i]))
                self._mcPt.push_back     (float(event.GenPart_pt[i]))
                self._mcEta.push_back    (float(event.GenPart_eta[i]))
                self._mcPhi.push_back    (float(event.GenPart_phi[i]))
                self._mcMass.push_back   (0.0)
                self._mcMomPID.push_back (0); self._mcGMomPID.push_back(0)
                self._mcStatusFlag.push_back(0)

            nLHEIn = int(getattr(event, "nLHEPart", 0))
            self._nLHE[0] = nLHEIn
            for i in range(nLHEIn):
                pt   = float(event.LHEPart_pt[i])
                eta  = float(event.LHEPart_eta[i])
                phi  = float(event.LHEPart_phi[i])
                mass = float(event.LHEPart_mass[i])
                self._lhePID.push_back(int(event.LHEPart_pdgId[i]))
                self._lhePx.push_back(pt * math.cos(phi))
                self._lhePy.push_back(pt * math.sin(phi))
                self._lhePz.push_back(pt * math.sinh(eta))
                self._lheE.push_back (math.sqrt((pt*math.cosh(eta))**2 + mass**2))

        self._tree.Fill()
        return False   # we filled manually; tell framework to skip its own Fill()
