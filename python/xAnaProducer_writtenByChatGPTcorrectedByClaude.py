import ROOT
import math
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class xAnaProducer(Module):

    def __init__(self, isMC=True):
        self.isMC = isMC

        ####################################
        # PRINT TRIGGER WARNING ONLY ONCE
        ####################################
        self.triggerWarningPrinted = False



    ########################################
    # BEGIN FILE
    ########################################

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        # Event-level
        self.out.branch("run", "I")
        self.out.branch("lumis", "I")              # xAna expects 'lumis'
        self.out.branch("event", "L")
        self.out.branch("rho", "F")
        self.out.branch("rhoAll", "F")
        self.out.branch("isPVGood", "O")
        self.out.branch("HLTEleMuX", "l")          # ULong64_t

        if self.isMC:
            # xAna expects a vector<float> 'puTrue'; we will fill [nTrue, nTrue]
            self.out.branch("puTrue", "F", lenVar="nPU2")
            self.out.branch("nPU2", "I")           # helper fixed length = 2
            self.out.branch("genWeight", "F")
            # Prefire placeholders (Run 3)
            self.out.branch("L1ECALPrefire", "D")
            self.out.branch("L1ECALPrefireUp", "D")
            self.out.branch("L1ECALPrefireDown", "D")
            self.out.branch("MuonPrefire", "D")
            self.out.branch("MuonPrefireUp", "D")
            self.out.branch("MuonPrefireDown", "D")

        # Muons (names/types xAna expects)
        self.out.branch("nMu", "I")
        for bname in [
            "muPt","muEta","muPhi","muEn",
            "muD0","muDz",
            "muBestTrkPtError","muBestTrkPt",
            "muSIP",
            "muPFChIso03","muPFPhoIso03","muPFNeuIso03","muPFPUIso03",
        ]:
            self.out.branch(bname, "F", lenVar="nMu")
        for bname in ["muCharge","muType","muTrkLayers","muBestTrkType","muPixelHits","muStations","muMatches"]:
            self.out.branch(bname, "I", lenVar="nMu")

        # Photons (xAna schema)
        self.out.branch("nPho", "I")
        for bname in [
            "phoE","phoEt","phoCalibEt","phoEta","phoPhi",
            "phoSCEta","phoSCPhi","phoIDMVA",
            "phoSCRawE","phoSigmaIEtaIEtaFull5x5","phoSCEtaWidth","phoSCPhiWidth",
            "phoSigmaIEtaIPhiFull5x5","phoPFPhoIso","phoPFChIso","phoPFChWorstIso",
            "phoS4Full5x5","phoE5x5Full5x5","phoESEffSigmaRR","phoESEnP1","phoESEnP2",
            "phoTrkIsoHollowConeDR03","phoHoverE",
            # variations: fill as nominal energies so variations are no-ops
            "phoScale_stat_up","phoScale_syst_up","phoScale_gain_up",
            "phoScale_stat_dn","phoScale_syst_dn","phoScale_gain_dn",
            "phoResol_phi_up","phoResol_rho_up","phoResol_rho_dn",
            # R9/MVA
            "phoCorrR9Full5x5","phoCorrHggIDMVA","phoR9Full5x5",
        ]:
            self.out.branch(bname, "F", lenVar="nPho")
        self.out.branch("phoEleVeto", "I", lenVar="nPho")

        # Jets (xAna schema)
        self.out.branch("nJet", "I")
        for bname in ["jetPt","jetEta","jetPhi","jetEn","jetNHF","jetNEF","jetID","jetCHF","jetCEF","jetMUF"]:
            self.out.branch(bname, "F", lenVar="nJet")
        for bname in ["jetNCH","jetNNP"]:
            self.out.branch(bname, "I", lenVar="nJet")
        if self.isMC:
            for bname in ["jetP4Smear","jetP4SmearUp","jetP4SmearDo","jetJECUnc"]:
                self.out.branch(bname, "F", lenVar="nJet")

        # Generator (minimal compatibility)
        if self.isMC:
            self.out.branch("nMC", "I")
            for bname, typ in [
                ("mcPID","I"),
                ("mcMomPID","I"),
                ("mcGMomPID","I"),
            ]:
                self.out.branch(bname, typ, lenVar="nMC")
            for bname in ["mcPt","mcEta","mcPhi","mcMass"]:
                self.out.branch(bname, "F", lenVar="nMC")
            self.out.branch("mcStatusFlag", "s", lenVar="nMC")  # unsigned short

            # LHE (empty ok if absent)
            self.out.branch("nLHE", "I")
            for bname, typ in [
                ("lhePID","I"),
                ("lheE","F"),
                ("lhePx","F"),
                ("lhePy","F"),
                ("lhePz","F"),
            ]:
                self.out.branch(bname, typ, lenVar="nLHE")

    def analyze(self, event):
        # Basic vertex
        isPVGood = (getattr(event, "PV_npvsGood", 0) > 0)
        if not isPVGood:
            return False

        # Trigger: map to HLTEleMuX bits
        mu17pho = False
        usedMu17Pho = None

        for name in [
            "HLT_Mu17_Photon30_IsoCaloId",
            "HLT_Mu17_Photon30",
            "HLT_Mu17_Photon30_CaloId",
            "HLT_Mu17_Photon30_CaloIdIso",
        ]:
            #if hasattr(event, name):
                #mu17pho = mu17pho or bool(getattr(event, name))

            try:
                val = bool(getattr(event, name))

                usedMu17Pho = name
                mu17pho = mu17pho or val
                break # stop once a valid branch is found            
            except RuntimeError:
                pass
                
                
        isomu = False
        usedIsoMu = None
        for name in ["HLT_IsoMu27","HLT_IsoMu24","HLT_Mu27"]:

            #if hasattr(event, name):
                #isomu = isomu or bool(getattr(event, name))

            try:
                val = bool(getattr(event, name))

                usedIsoMu = name
                isomu = isomu or val
                break # stop once a valid branch is found                
            except RuntimeError:
                pass


        # -------------------------------------------------
        # Print trigger information only once
        # -------------------------------------------------
        if not self.triggerWarningPrinted:
            # Preferred trigger exists
            if usedMu17Pho is not None:
                print(
                    f"\033[92m[INFO] Using Mu17+Photon trigger: "
                    f"{usedMu17Pho}\033[0m"
                )
            # Fallback to IsoMu
            
            elif usedIsoMu is not None:
                print(
                    "\033[93m[WARN] No Mu17+Photon trigger branch found.\033[0m"
                )
                print(
                    f"\033[93m[WARN] Falling back to IsoMu trigger: "
                    f"{usedIsoMu}\033[0m"
                )
                # Nohing found
            else:
                print(
                    "\033[91m[ERROR] Neither Mu17+Photon nor IsoMu "
                    "trigger branches were found.\033[0m"
                )
            
            self.triggerWarningPrinted = True
            
        HLTEleMuX = (int(mu17pho) << 8) | (int(isomu) << 19)

        # If none of the expected HLT branches exist, warn once
#        if not self.triggerWarningPrinted and not any(hasattr(event, n) for n in
#                                                     ["HLT_Mu17_Photon30_IsoCaloId","HLT_IsoMu27","HLT_IsoMu24","HLT_Mu27"]):
 #           print("\033[93m[WARN] No recognized HLT_* branches found for Mu17+Pho30 or IsoMu paths in this file.\033[0m")
#            self.triggerWarningPrinted = True

        # Analysis-time HLT pass: require Mu17+Pho30 (to mirror your original behavior)

        #if not mu17pho :
        if not (mu17pho or isomu):
            return False

        # Event-level fills
        self.out.fillBranch("run", event.run)
        self.out.fillBranch("lumis", event.luminosityBlock)
        self.out.fillBranch("event", event.event)

        rho = getattr(event, "Rho_fixedGridRhoFastjetAll", 0.0)
        self.out.fillBranch("rho", rho)
        self.out.fillBranch("rhoAll", rho)
        self.out.fillBranch("isPVGood", True)
        self.out.fillBranch("HLTEleMuX", HLTEleMuX)

        if self.isMC:
            self.out.fillBranch("genWeight", getattr(event, "genWeight", 1.0))
            # puTrue vector with at least two entries (duplicate nTrue)
            nTrue = float(getattr(event, "Pileup_nTrueInt", 0.0))
            self.out.fillBranch("nPU2", 2)
            self.out.fillBranch("puTrue", [nTrue, nTrue])
            # Prefire placeholders (Run 3)
            for k in ["L1ECALPrefire","L1ECALPrefireUp","L1ECALPrefireDown",
                      "MuonPrefire","MuonPrefireUp","MuonPrefireDown"]:
                self.out.fillBranch(k, 1.0)

        # Muons: build arrays
        muPt=[]; muEta=[]; muPhi=[]; muEn=[]
        muD0=[]; muDz=[]; muBestTrkPt=[]; muBestTrkPtError=[]
        muSIP=[]; muPFChIso03=[]; muPFPhoIso03=[]; muPFNeuIso03=[]; muPFPUIso03=[]
        muCharge=[]; muType=[]; muTrkLayers=[]; muBestTrkType=[]; muPixelHits=[]; muStations=[]; muMatches=[]

        nMuon = getattr(event, "nMuon", 0)
        for i in range(nMuon):
            pt  = event.Muon_pt[i]
            eta = event.Muon_eta[i]
            phi = event.Muon_phi[i]
            m   = getattr(event, "Muon_mass", [0.1057]*nMuon)[i]
            if pt < 5 or abs(eta) > 2.4:
                continue

            muPt.append(pt); muEta.append(eta); muPhi.append(phi)
            en = math.sqrt((pt*math.cosh(eta))**2 + m**2)
            muEn.append(en)

            muCharge.append(event.Muon_charge[i])
            muD0.append(getattr(event, "Muon_dxy", [0]*nMuon)[i])
            muDz.append(getattr(event, "Muon_dz", [0]*nMuon)[i])
            muBestTrkPt.append(pt)
            muBestTrkPtError.append(0.0)
            muSIP.append(abs(getattr(event, "Muon_sip3d", [0]*nMuon)[i]))

            # PF iso components — set what we have, rest 0
            rel03_chg = getattr(event, "Muon_pfRelIso03_chg", None)
            if rel03_chg is not None:
                muPFChIso03.append(rel03_chg[i]*pt)
            else:
                muPFChIso03.append(0.0)
            muPFPhoIso03.append(0.0)
            muPFNeuIso03.append(0.0)
            muPFPUIso03.append(0.0)

            # muType bits: bit1 Global, bit2 Tracker, bit5 PF
            itype = 0
            if getattr(event, "Muon_isGlobal", [0]*nMuon)[i]:  itype |= (1<<1)
            if getattr(event, "Muon_isTracker", [0]*nMuon)[i]: itype |= (1<<2)
            if getattr(event, "Muon_isPFcand", [0]*nMuon)[i]:  itype |= (1<<5)
            muType.append(itype)

            #muTrkLayers.append(getattr(event, "Muon_nTrackerLayers", [0]*nMuon)[i])
            muTrkLayers.append(ord(getattr(event, "Muon_nTrackerLayers", [0]*nMuon)[i]))
            muBestTrkType.append(1)  # placeholder
#            muPixelHits.append(getattr(event, "Muon_nPixelHits", [0]*nMuon)[i])
            muStations.append(ord(getattr(event, "Muon_nStations", [0]*nMuon)[i]))
#            muMatches.append(getattr(event, "Muon_nMatches", [0]*nMuon)[i])
            try:
                muMatches.append(event.Muon_nMatches[i])
            except RuntimeError:
                muMatches.append(0)
            try:
                muPixelHits.append(event.Muon_nPixelHits[i])
            except RuntimeError:
                muPixelHits.append(0)
            
        if len(muPt) < 2:
            return False

        # Photons
        phoE=[]; phoEt=[]; phoCalibEt=[]; phoEta=[]; phoPhi=[]
        phoSCEta=[]; phoSCPhi=[]; phoIDMVA=[]
        phoSCRawE=[]; phoSigmaIEtaIEtaFull5x5=[]; phoSCEtaWidth=[]; phoSCPhiWidth=[]
        phoSigmaIEtaIPhiFull5x5=[]; phoPFPhoIso=[]; phoPFChIso=[]; phoPFChWorstIso=[]
        phoS4Full5x5=[]; phoE5x5Full5x5=[]; phoESEffSigmaRR=[]; phoESEnP1=[]; phoESEnP2=[]
        phoTrkIsoHollowConeDR03=[]; phoHoverE=[]
        # variations
        phoScale_stat_up=[]; phoScale_syst_up=[]; phoScale_gain_up=[]
        phoScale_stat_dn=[]; phoScale_syst_dn=[]; phoScale_gain_dn=[]
        phoResol_phi_up=[]; phoResol_rho_up=[]; phoResol_rho_dn=[]
        # R9/MVA
        phoCorrR9Full5x5=[]; phoCorrHggIDMVA=[]; phoR9Full5x5=[]
        phoEleVeto=[]

        nPho = getattr(event, "nPhoton", 0)
        for i in range(nPho):
            pt  = event.Photon_pt[i]
            eta = event.Photon_eta[i]
            phi = event.Photon_phi[i]
#            m   = getattr(event, "Photon_mass", [0.0]*nPho)[i]
            m=0.0
            
            if pt < 10 or abs(eta) > 2.5:
                continue

            E = math.sqrt((pt*math.cosh(eta))**2 + m**2)
            phoE.append(E); phoEt.append(pt); phoCalibEt.append(pt)
            phoEta.append(eta); phoPhi.append(phi)
            phoSCEta.append(eta); phoSCPhi.append(phi)
            phoIDMVA.append(float(getattr(event, "Photon_mvaID", [ -99.0 ]*nPho)[i]))
            phoEleVeto.append(int(getattr(event, "Photon_electronVeto", [0]*nPho)[i]))
            phoSCRawE.append(E)  # proxy if raw not available
            phoSigmaIEtaIEtaFull5x5.append(float(getattr(event, "Photon_sieie", [0.0]*nPho)[i]))
            phoSCEtaWidth.append(0.0); phoSCPhiWidth.append(0.0)
            phoSigmaIEtaIPhiFull5x5.append(float(getattr(event, "Photon_sieip", [0.0]*nPho)[i]))
            phoPFPhoIso.append(0.0); phoPFChIso.append(0.0); phoPFChWorstIso.append(0.0)
            phoS4Full5x5.append(float(getattr(event, "Photon_s4", [0.0]*nPho)[i]))
            phoE5x5Full5x5.append(float(1.0))            # E5x5 is being set always to 1, as later in xAna.C we will need to have E2x2/E5x5, E2x2 and E5x5 is obsolete in nanoAOD, and rather s4 is stored, so we can use s4/E5x5 later.
            phoESEffSigmaRR.append(0.0); phoESEnP1.append(0.0); phoESEnP2.append(0.0)
            phoTrkIsoHollowConeDR03.append(0.0)
            phoHoverE.append(float(getattr(event, "Photon_hoe", [0.0]*nPho)[i]))
            # Variations as nominal energies (so xAna variations are defined but no-op)
            phoScale_stat_up.append(E); phoScale_syst_up.append(E); phoScale_gain_up.append(E)
            phoScale_stat_dn.append(E); phoScale_syst_dn.append(E); phoScale_gain_dn.append(E)
            phoResol_phi_up.append(E); phoResol_rho_up.append(E); phoResol_rho_dn.append(E)
            # R9 / MVA
            r9 = float(getattr(event, "Photon_r9", [0.0]*nPho)[i])
            phoCorrR9Full5x5.append(r9); phoR9Full5x5.append(r9)
            phoCorrHggIDMVA.append(-99.0)

        if len(phoEt) < 1:
            return False

        # Jets
        jetPt=[]; jetEta=[]; jetPhi=[]; jetEn=[]
        jetNHF=[]; jetNEF=[]; jetID=[]; jetCHF=[]; jetCEF=[]; jetMUF=[]
        jetNCH=[]; jetNNP=[]
        jetP4Smear=[]; jetP4SmearUp=[]; jetP4SmearDo=[]; jetJECUnc=[]

        nJet = getattr(event, "nJet", 0)
        for i in range(nJet):
            pt  = event.Jet_pt[i]
            eta = event.Jet_eta[i]
            phi = event.Jet_phi[i]
            m   = getattr(event, "Jet_mass", [0.0]*nJet)[i]
            if pt < 20:
                continue
            jetPt.append(pt); jetEta.append(eta); jetPhi.append(phi)
            E = math.sqrt((pt*math.cosh(eta))**2 + m**2)
            jetEn.append(E)

            jetNHF.append(float(getattr(event, "Jet_neHEF", [0.0]*nJet)[i]))
            jetNEF.append(float(getattr(event, "Jet_neEmEF", [0.0]*nJet)[i]))
            jetCHF.append(float(getattr(event, "Jet_chHEF", [0.0]*nJet)[i]))
            jetCEF.append(float(getattr(event, "Jet_chEmEF", [0.0]*nJet)[i]))
            jetMUF.append(float(getattr(event, "Jet_muEF", [0.0]*nJet)[i]))
            #jetNCH.append(int(getattr(event, "Jet_chMultiplicity", [0]*nJet)[i]))
            val = getattr(event, "Jet_chMultiplicity", [0]*nJet)[i]
            jetNCH.append(ord(val) if isinstance(val, str) else int(val))
            #jetNCH.append(ord(getattr(event, "Jet_chMultiplicity", [0]*nJet)[i]))
            #jetNNP.append(int(getattr(event, "Jet_neMult", [0]*nJet)[i]))
            val = getattr(event, "Jet_neMultiplicity", [0]*nJet)[i]
            jetNNP.append(ord(val) if isinstance(val, str) else int(val))
            #jetNNP.append(ord(getattr(event, "Jet_neMultiplicity", [0]*nJet)[i]))
            #jid = int(getattr(event, "Jet_jetId", [0]*nJet)[i])
            jid=4
            jetID.append(1 if jid >= 4 else 0)
            if self.isMC:
                jetP4Smear.append(1.0); jetP4SmearUp.append(1.0); jetP4SmearDo.append(1.0); jetJECUnc.append(0.0)

        # Fill muons
        self.out.fillBranch("nMu", len(muPt))
        for name, arr in [
            ("muPt",muPt),("muEta",muEta),("muPhi",muPhi),("muEn",muEn),
            ("muD0",muD0),("muDz",muDz),
            ("muBestTrkPtError",muBestTrkPtError),("muBestTrkPt",muBestTrkPt),
            ("muSIP",muSIP),
            ("muPFChIso03",muPFChIso03),("muPFPhoIso03",muPFPhoIso03),("muPFNeuIso03",muPFNeuIso03),("muPFPUIso03",muPFPUIso03),
            ("muCharge",muCharge),("muType",muType),("muTrkLayers",muTrkLayers),("muBestTrkType",muBestTrkType),
            ("muPixelHits",muPixelHits),("muStations",muStations),("muMatches",muMatches),
        ]:
            #self.out.fillBranch(name, arr)
            try:
                self.out.fillBranch(name, arr)

            except Exception as e:
                print("\n================ DEBUG ================")
                print("Branch :", name)
                
                if len(arr) > 0:
                    print("First entry :", arr[0])
                    print("Type        :", type(arr[0]))
                    
                    print("Exception   :", e)
                    print("=======================================\n")                    
                    raise

        # Fill photons
        self.out.fillBranch("nPho", len(phoEt))
        for name, arr in [
            ("phoE",phoE),("phoEt",phoEt),("phoCalibEt",phoCalibEt),("phoEta",phoEta),("phoPhi",phoPhi),
            ("phoSCEta",phoSCEta),("phoSCPhi",phoSCPhi),("phoIDMVA",phoIDMVA),
            ("phoSCRawE",phoSCRawE),("phoSigmaIEtaIEtaFull5x5",phoSigmaIEtaIEtaFull5x5),
            ("phoSCEtaWidth",phoSCEtaWidth),("phoSCPhiWidth",phoSCPhiWidth),("phoSigmaIEtaIPhiFull5x5",phoSigmaIEtaIPhiFull5x5),
            ("phoPFPhoIso",phoPFPhoIso),("phoPFChIso",phoPFChIso),("phoPFChWorstIso",phoPFChWorstIso),
            ("phoS4Full5x5",phoS4Full5x5),("phoE5x5Full5x5",phoE5x5Full5x5),
            ("phoESEffSigmaRR",phoESEffSigmaRR),("phoESEnP1",phoESEnP1),("phoESEnP2",phoESEnP2),
            ("phoTrkIsoHollowConeDR03",phoTrkIsoHollowConeDR03),("phoHoverE",phoHoverE),
            ("phoScale_stat_up",phoScale_stat_up),("phoScale_syst_up",phoScale_syst_up),("phoScale_gain_up",phoScale_gain_up),
            ("phoScale_stat_dn",phoScale_stat_dn),("phoScale_syst_dn",phoScale_syst_dn),("phoScale_gain_dn",phoScale_gain_dn),
            ("phoResol_phi_up",phoResol_phi_up),("phoResol_rho_up",phoResol_rho_up),("phoResol_rho_dn",phoResol_rho_dn),
            ("phoCorrR9Full5x5",phoCorrR9Full5x5),("phoCorrHggIDMVA",phoCorrHggIDMVA),("phoR9Full5x5",phoR9Full5x5),
            ("phoEleVeto",phoEleVeto),
        ]:
            #self.out.fillBranch(name, arr)
            try:
                self.out.fillBranch(name, arr)

            except Exception as e:
                print("\n================ DEBUG ================")
                print("Branch :", name)

                if len(arr) > 0:
                    print("First entry :", arr[0])
                    print("Type        :", type(arr[0]))

                print("Exception   :", e)
                print("=======================================\n")

                raise

        # Fill jets
        self.out.fillBranch("nJet", len(jetPt))
        for name, arr in [
            ("jetPt",jetPt),("jetEta",jetEta),("jetPhi",jetPhi),("jetEn",jetEn),
            ("jetNHF",jetNHF),("jetNEF",jetNEF),("jetID",jetID),("jetCHF",jetCHF),("jetCEF",jetCEF),("jetMUF",jetMUF),
            ("jetNCH",jetNCH),("jetNNP",jetNNP),
        ]:
            self.out.fillBranch(name, arr)
        if self.isMC:
            for name, arr in [
                ("jetP4Smear",jetP4Smear),("jetP4SmearUp",jetP4SmearUp),("jetP4SmearDo",jetP4SmearDo),("jetJECUnc",jetJECUnc),
            ]:
                #self.out.fillBranch(name, arr)
                try:
                    self.out.fillBranch(name, arr)

                except Exception as e:

                    print("\n================ DEBUG ================")
                    print("Branch :", name)

                    if len(arr) > 0:
                        print("First entry :", arr[0])
                        print("Type        :", type(arr[0]))

                    print("Exception   :", e)
                    print("=======================================\n")

                    raise
                    
        # Generator
        if self.isMC:
            nGen = getattr(event, "nGenPart", 0)
            mcPID=[]; mcMomPID=[]; mcGMomPID=[]; mcPt=[]; mcEta=[]; mcPhi=[]; mcMass=[]; mcStatusFlag=[]
            for i in range(nGen):
                mcPID.append(int(event.GenPart_pdgId[i]))
                mcPt.append(float(event.GenPart_pt[i]))
                mcEta.append(float(event.GenPart_eta[i]))
                mcPhi.append(float(event.GenPart_phi[i]))
                mcMass.append(0.0)
                mcMomPID.append(0)
                mcGMomPID.append(0)
                mcStatusFlag.append(0)
            self.out.fillBranch("nMC", len(mcPID))
            for name, arr in [
                ("mcPID",mcPID),("mcMomPID",mcMomPID),("mcGMomPID",mcGMomPID),
                ("mcPt",mcPt),("mcEta",mcEta),("mcPhi",mcPhi),("mcMass",mcMass),
                ("mcStatusFlag",mcStatusFlag),
            ]:
                self.out.fillBranch(name, arr)
                
            # LHE — fill empty if not available
            nLHE = int(getattr(event, "nLHEPart", 0))
            if nLHE > 0:
                pid = [int(event.LHEPart_pdgId[i]) for i in range(nLHE)]
                pt  = [float(event.LHEPart_pt[i]) for i in range(nLHE)]
                eta = [float(event.LHEPart_eta[i]) for i in range(nLHE)]
                phi = [float(event.LHEPart_phi[i]) for i in range(nLHE)]
                mass= [float(event.LHEPart_mass[i]) for i in range(nLHE)]
                px   = [pt[i]*math.cos(phi[i]) for i in range(nLHE)]
                py   = [pt[i]*math.sin(phi[i]) for i in range(nLHE)]
                pz   = [pt[i]*math.sinh(eta[i]) for i in range(nLHE)]
                E    = [math.sqrt(pt[i]**2*math.cosh(eta[i])**2 + mass[i]**2) for i in range(nLHE)]
                self.out.fillBranch("nLHE", nLHE)
                self.out.fillBranch("lhePID", pid)
                self.out.fillBranch("lhePx", px)
                self.out.fillBranch("lhePy", py)
                self.out.fillBranch("lhePz", pz)
                self.out.fillBranch("lheE", E)
            else:
                self.out.fillBranch("nLHE", 0)
                self.out.fillBranch("lhePID", [])
                self.out.fillBranch("lhePx", [])
                self.out.fillBranch("lhePy", [])
                self.out.fillBranch("lhePz", [])
                self.out.fillBranch("lheE", [])

        return True
