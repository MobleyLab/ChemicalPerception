"""
This test is created to check how a single molecule SMIRKS graph works
"""

from chemper.graphs.fragment_graph import ChemPerGraphFromMol
from chemper.graphs.cluster_graph import ClusterGraph
from chemper.mol_toolkits import mol_toolkit
import pytest


def make_frag_graph(smiles, layers):
    mol = mol_toolkit.MolFromSmiles(smiles)
    smirks_dict = {1:0, 2:1}
    return ChemPerGraphFromMol(mol, smirks_dict, layers)

def make_cluster_graph(smiles_list, layers=0):
    smirks_dict_list = [[{1:0, 2:1}]]*len(smiles_list)
    mols_list = [mol_toolkit.MolFromSmiles(smiles) for smiles in smiles_list]
    return ClusterGraph(mols_list, smirks_dict_list, layers=layers)


insideH = "(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])"
outsideH = "(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])-;!@[#1AH0X1x0r0+0]"
graph_data = [
    (make_frag_graph('C', 0), '[#6AH4X4x0r0+0:1]-!@[#1AH0X1x0r0+0:2]'), # no layers
    (make_frag_graph('C#C', 1), # one layer
     '[#6AH1X2x0r0+0:1](-!@[#1AH0X1x0r0+0])#!@[#6AH1X2x0r0+0:2]-!@[#1AH0X1x0r0+0]'),
    (make_frag_graph('CO', 'all'), # infinite layers
     '[#6AH3X4x0r0+0:1](-!@[#1AH0X1x0r0+0])(-!@[#1AH0X1x0r0+0])(-!@[#1AH0X1x0r0+0])'\
     '-!@[#8AH1X2x0r0+0:2]-!@[#1AH0X1x0r0+0]'
     ),
    (make_cluster_graph(['CC']), "[#6AH3X4x0r0+0:1]-;!@[#6AH3X4x0r0+0:2]"),
    (make_cluster_graph(['CC', 'C=C']),
     "[#6AH2X3x0r0+0,#6AH3X4x0r0+0:1]-,=;!@[#6AH2X3x0r0+0,#6AH3X4x0r0+0:2]"),
    (make_cluster_graph(['CC', 'C=C', 'C1CC1']),
     "[#6AH2X3x0r0+0,#6AH2X4x2r3+0,#6AH3X4x0r0+0:1]-,=[#6AH2X3x0r0+0,#6AH2X4x2r3+0,#6AH3X4x0r0+0:2]"),
    (make_cluster_graph(['CC'], layers=1),
     "[#6AH3X4x0r0+0:1]%s-;!@[#6AH3X4x0r0+0:2]%s" % (insideH, outsideH) ),
    (make_cluster_graph(['CC'], layers='all'),
     "[#6AH3X4x0r0+0:1]%s-;!@[#6AH3X4x0r0+0:2]%s" % (insideH, outsideH) ),
    (make_cluster_graph(['C#C'], 1), # one layer
     '[#6AH1X2x0r0+0:1](-;!@[#1AH0X1x0r0+0])#;!@[#6AH1X2x0r0+0:2]-;!@[#1AH0X1x0r0+0]'),
    (make_cluster_graph(['CO'], 'all'), # infinite layers
     '[#6AH3X4x0r0+0:1](-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])' \
     '-;!@[#8AH1X2x0r0+0:2]-;!@[#1AH0X1x0r0+0]'
     ),
    (make_cluster_graph(['C#CC'], 3), # one layer
     '[#6AH1X2x0r0+0:1](-;!@[#1AH0X1x0r0+0])#;!@[#6AH0X2x0r0+0:2]-;!@[#6AH3X4x0r0+0]%s' % outsideH),
]


@pytest.mark.parametrize('graph,expected', graph_data)
def test_smirks_frag_graph(graph, expected):
    smirks = graph.as_smirks()
    print(smirks)
    assert smirks == expected

@pytest.mark.parametrize('graph', [g for g,e in graph_data])
def test_other_cluster_graph(graph):
    bonds = graph.get_bonds()
    atom = graph.get_atoms()[0]
    neighbor = graph.get_neighbors(atom)[0]
    bond = graph.get_connecting_bond(atom, neighbor)
    assert bond is not None


# test layered cluster graphs where order isn't determined
outsideHC1 = "(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0,#6AH3X4x0r0+0])-;!@[#1AH0X1x0r0+0]"
outsideHC2 = "(-;!@[#1AH0X1x0r0+0,#6AH3X4x0r0+0])(-;!@[#1AH0X1x0r0+0])-;!@[#1AH0X1x0r0+0]"
outsideHC3 = "(-;!@[#1AH0X1x0r0+0])(-;!@[#1AH0X1x0r0+0])-;!@[#1AH0X1x0r0+0,#6AH3X4x0r0+0]"
cluster_graphs = [
    (make_cluster_graph(['CC', 'CCC'], layers=1), [
        "[#6AH3X4x0r0+0:1]%s-;!@[#6AH2X4x0r0+0,#6AH3X4x0r0+0:2]%s" % (insideH, outsideHC1),
        "[#6AH3X4x0r0+0:1]%s-;!@[#6AH2X4x0r0+0,#6AH3X4x0r0+0:2]%s" % (insideH, outsideHC2),
        "[#6AH3X4x0r0+0:1]%s-;!@[#6AH2X4x0r0+0,#6AH3X4x0r0+0:2]%s" % (insideH, outsideHC3),
    ]),
]
@pytest.mark.parametrize('graph,expected', cluster_graphs)
def test_layered_clusters(graph, expected):
    smirks = graph.as_smirks()
    print(smirks)
    assert smirks in expected


# make sure corner cases can at least be built without failing
smiles = [['C', 'c1ccccc1'], ['C1CC1F', 'OC(=O)CC'], ['c1ccccc1', 'Oc1ccccc1']]
layers_options = [1,2,3,4,5,'all']
combos = [(s,l) for s in smiles for l in layers_options]

@pytest.mark.parametrize('smiles_list,layers', combos)
def test_no_failing(smiles_list, layers):
    smirks_dict_list = [[{1: 0, 2: 1}, {1:1, 2:2}]] * len(smiles_list)
    mols_list = [mol_toolkit.MolFromSmiles(s) for s in smiles_list]
    ClusterGraph(mols_list, smirks_dict_list, layers=layers)