addiction_d = {"reward":"reward|hedonic|incentive|intracranial self stimulation|ICSS|reinforcement|reinforcing|conditioned place preference|CPP|self administration|self administered|drug reinforced|operant|instrumental response",
        "aversion":"aversion|aversive|CTA|conditioned taste aversion",
        "withdrawal":"withdrawal",
        "relapse":"relapse|reinstatement|craving|drug seeking|seeking",
        "sensitization":"sensitization",
        "addiction":"addiction|addictive|drug abuse|punishment|compulsive|escalation",
        "dependence":"dependence",
        "intoxication":"intoxication|binge"
        }
drug_d = {"alcohol":"alcohol|alcoholism|alcoholic|alcoholics",
        "nicotine":"smoking|nicotine|tobacco|smoker|smokers",
        "cocaine":"cocaine",
        "opioid":"opioid|opioids|fentanyl|oxycodone|oxycontin|heroin|morphine|methadone|buprenorphine|vicodin|hydrocodone|hycodan|kadian|percoset|hydromorphone|naloxone|codeine|suboxone|tramadol|kratom|ultram",
        "amphetamine":"methamphetamine|amphetamine|METH|AMPH",
        "cannabinoid":"endocannabinoid|cannabinoids|cannabis|endocannabinoids|marijuana|cannabidiol|cannabinoid|tetrahydrocannabinol|thc|thc 9|Oleoylethanolamide|palmitoylethanolamide|acylethanolamides"
        }
brain_d ={"cortex":"cortex|prefrontal|pfc|mPFC|vmpfc|corticostriatal|cortico limbic|corticolimbic|prl|prelimbic|infralimbic|orbitofrontal|cingulate|cerebral|insular|insula",
          "striatum":"striatum|STR|striatal|caudate|putamen|basal ganglia|globus pallidus|GPI",
          "accumbens":"accumbens|accumbal|shell|core|Nacc|NacSh|acbs|acbc",
          "hippocampus":"hippocampus|hippocampal|hipp|hip|ca1|ca3|dentate gyrus|subiculum|vhipp|dhpc|vhpc",
          "amygdala":"amygdala|cea|bla|amy|cna",
          "VTA":"ventral tegmental|vta|pvta|mesolimbic|limbic|midbrain|mesoaccumbens|mesoaccumbal",
          "habenula":"habenula|lhb|mhb",
          "hypothalamus":"hypothalamus|hypothalamic|PVN|paraventricular nucleus|LHA"
          }
# brain region has too many short acronyms to just use the undic function, so search PubMed using the following 
brain_query_term="cortex|accumbens|striatum|amygadala|hippocampus|tegmental|mesolimbic|infralimbic|prelimbic|habenula"
function_d={"signalling":"signalling|signaling|phosphorylation|glycosylation",
            "transcription":"transcription|methylation|hypomethylation|hypermethylation|histone|ribosome",
            "neuroplasticity":"neuroplasticity|plasticity|long term potentiation|LTP|long term depression|LTD|synaptic|epsp|epsc|neurite|neurogenesis|boutons|mIPSC|IPSC|IPSP",
            "neurotransmission": "neurotransmission|neuropeptides|neuropeptide|glutamate|glutamatergic|GABA|GABAergic|dopamine|dopaminergic|DAergic|cholinergic|nicotinic|muscarinic|serotonergic|serotonin|5 ht|acetylcholine",
            }
#"regulation":"increased|decreased|regulated|inhibited|stimulated",
