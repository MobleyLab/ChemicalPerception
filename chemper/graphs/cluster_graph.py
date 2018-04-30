"""
fragment_graph.py

ChemPerGraph are a class for tracking molecular fragments based on information about the atoms and bonds they contain.
You can combine them or take a difference in order to find distinguishing characteristics in a set of clustered
molecular sub-graphs.

AUTHORS:

Caitlin C. Bannan <bannanc@uci.edu>, Mobley Group, University of California Irvine
"""

# TODO: import mol_toolkit?
import networkx as nx
from chemper.graphs.fragment_graph import ChemPerGraph


class ClusterGraph(ChemPerGraph):
    """
    ChemPerGraphs are a graph based class for storing atom and bond information.
    They use the chemper.mol_toolkits Atoms, Bonds, and Mols
    """
    class AtomStorage(object):
        """
        AtomStorage tracks information about an atom
        """
        def __init__(self, atoms=None, smirks_index=None):
            """
            """
            self.decorators = set()
            if atoms is not None:
                for atom in atoms:
                    self.decorators.add(self.make_atom_decorators(atom))
            self.smirks_index = smirks_index

        def make_atom_decorators(self, atom):
            aromatic = 'a' if atom.is_aromatic() else 'A'
            charge = atom.formal_charge()
            if charge >= 0:
                charge = '+%i' % charge
            else:
                charge = '%i' % charge

            return (
                '#%i' % atom.atomic_number(),
                aromatic,
                'H%i' % atom.hydrogen_count(),
                'X%i' % atom.connectivity(),
                'x%i' % atom.ring_connectivity(),
                'r%i' % atom.min_ring_size(),
                charge
                )

        def as_smirks(self):
            """
            :return: smirks pattern for this atom
            """
            if len(self.decorators) == 0:
                if self.smirks_index is None or self.smirks_index <= 0:
                    return '[*]'
                return '[*:%i]' % self.smirks_index

            base_smirks = ','.join([''.join(l) for l in sorted(list(self.decorators))])
            if self.smirks_index is None or self.smirks_index <= 0:
                return '[%s]' % base_smirks

            return '[%s:%i]' % (base_smirks, self.smirks_index)

        def add_atom(self, atom):
            self.decorators.add(self.make_atom_decorators(atom))

    class BondStorage(object):
        """
        BondStorage tracks information about a bond
        """
        def __init__(self, bonds=None, smirks_index=None):
            self.order = set()
            self.ring = set()
            self.order_dict = {1:'-', 1.5:':', 2:'=', 3:'#'}
            if bonds is not None:
                for bond in bonds:
                    self.order.add(self.order_dict.get(bond.get_order()))
                    self.ring.add(bond.is_ring())

            self.smirks_index = smirks_index

        def as_smirks(self):
            """
            :return: string of how this bond should appear in a SMIRKS string
            """
            if len(self.order) == 0:
                order = '~'
            else:
                order = ','.join(sorted(list(self.order)))

            if len(self.ring) == 1:
                if list(self.ring)[0]:
                    return order+';@'
                else:
                    return order+';!@'

            return order

        def add_bond(self, bond):
            """
            adds decorators for another bond
            :param bond: chemper mol_toolkit Bond object
            """
            self.order.add(self.order_dict.get(bond.get_order()))
            self.ring.add(bond.is_ring())

    # Initiate ClusterGraph
    def __init__(self, mols=None, smirks_atoms_lists=None, layers=0):
        # TODO: figure out layers, currently only supporting layers=0
        """
        Initialize a ChemPerGraph from a molecule and a set of indexed atoms

        :param mols: list of chemper mols
        :param smirks_atoms_lists: sorted by mol list of lists of dictionary of the form {smirks_index: atom_index}
        # TODO: figure out the best form for the smirks_atoms_lists
        :param layers: how many atoms out from the smirks indexed atoms do you wish save (default=0)
                       'all' will lead to all atoms in the molecule being specified (not recommended)
        """
        ChemPerGraph.__init__(self)

        self.mols = list()
        self.smirks_atoms_lists = list()

        if mols is not None:
            if len(mols) != len(smirks_atoms_lists):
                raise Exception('Number of molecules and smirks dictionaries should be equal')

            self._add_first_smirks_atoms(mols[0], smirks_atoms_lists[0])
            for idx, mol in enumerate(mols[1:]):
                self.add_mol(mol, smirks_atoms_lists[idx])

        # TODO: figure out how to extend beyond just "SMIRKS indexed" atoms
        # self.atom_by_index = dict()
        #for smirks_key, atom_storage in self.atom_by_smirks_index.items():
        #    self._add_layers(atom_storage, layers)

    def _add_first_smirks_atoms(self, mol, smirks_atoms_list):
        self.mols.append(mol)
        self.smirks_atoms_lists.append(smirks_atoms_list)

        for smirks_atoms in smirks_atoms_list:
            # add all smirks atoms to the graph
            for key, atom_index in smirks_atoms.items():
                atom1 = mol.get_atom_by_index(atom_index)
                new_atom_storage = self.AtomStorage([atom1], key)
                self._graph.add_node(new_atom_storage)
                self.atom_by_smirks_index[key] = new_atom_storage
                # self.atom_by_index[atom_index] = new_atom_storage

                # Check for bonded atoms already in the graph
                for neighbor_key, neighbor_index in smirks_atoms.items():
                    if not neighbor_key in self.atom_by_smirks_index:
                        continue
                    atom2 = mol.get_atom_by_index(neighbor_index)
                    bond = mol.get_bond_by_atoms(atom1, atom2)

                    if bond is not None: # Atoms are connected add edge
                        bond_smirks = max(neighbor_key, key)-1
                        bond_storage = self.BondStorage([bond], bond_smirks)
                        self.bond_by_smirks_index[bond_smirks] = bond_storage
                        self._graph.add_edge(new_atom_storage,
                                             self.atom_by_smirks_index[neighbor_key],
                                             bond=bond_storage)

    def add_mol(self, mol, smirks_atoms_list):
        """
        :param mol:
        :param smirks_atoms:
        :return:
        """
        self.mols.append(mol)
        self.smirks_atoms_lists.append(smirks_atoms_list)

        for smirks_atoms in smirks_atoms_list:
            for key, atom_index in smirks_atoms.items():
                atom1 = mol.get_atom_by_index(atom_index)
                self.atom_by_smirks_index[key].add_atom(atom1)

                for neighbor_key, neighbor_index in smirks_atoms.items():
                    # check for connecting bond
                    atom2 = mol.get_atom_by_index(neighbor_index)
                    bond = mol.get_bond_by_atoms(atom1, atom2)
                    if bond is not None:
                        bond_smirks = max(neighbor_key, key) - 1
                        self.bond_by_smirks_index[bond_smirks].add_bond(bond)