"""
This script decompose all the articles associated to a projects and parse technical data

For extract new technical data, you need to add a new feature extraction function
using the decorator the same format as the other functions.

Just remember:
    - The function takes as input the dataframe of all the articles associated to a project and the related tree
    - The function returns a dictionary with the new features
    - Add the decorator @extract_features before the function

The feature will be added to the database in the table "SPEC_EQUIP".
Make attention: all values will be converted to string
(this is a well known issue in designing EAV tables, this seems to me the best solution, Divalto use it too)
That's all folks !

"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from db_utils.base import Session_ax, Session
from db_utils.tables import SpecEquipM
import pandas as pd
import re
from db_utils.utils import get_equips
from log_init import make_logger
from tqdm import tqdm
import traceback

logger = make_logger('spec_equipement')
from treelib import Tree


def level_order_traversal(tree):
    """
    Perform a level-order traversal on a treelib Tree object.

    This function traverses the tree in a breadth-first manner, ensuring that
    all nodes are visited in a sequence where each child node is listed after
    its parent node. The function returns a list of node tags in the order
    they were visited.

    Parameters:
    tree (treelib.Tree): A treelib Tree object.

    Returns:
    list: A list of node tags representing the level-order traversal of the tree.
    """

    # List to store the level-order traversal
    nodes_in_order = []
    # Get the root node
    root_node = tree.get_node(tree.root)
    # Queue for level-order traversal
    queue = [root_node]
    while queue:
        # Pop the first node from the queue
        current_node = queue.pop(0)
        # Add it to the nodes_in_order list
        nodes_in_order.append(current_node.tag)
        # Add child nodes of the current node to the queue
        for child_id in tree.children(current_node.identifier):
            queue.append(child_id)
    return nodes_in_order


def find_distance(tree, node1_id, node2_id):
    """
    Find the last common ancestor between two nodes in a tree.

    Args:
        tree (Tree): The Tree object representing the tree.
        node1_id (str): ID of the first node.
        node2_id (str): ID of the second node.

    Returns:
        str: ID of the last common ancestor node, or None if no common ancestor is found.
    """

    # Find the last common ancestor

    last_ancestor = node1_id
    while last_ancestor is not tree.root:
        if tree.is_ancestor(last_ancestor, node2_id):
            break
        last_ancestor = tree.parent(last_ancestor).identifier

    node1_depth = tree.depth(node1_id)
    node2_depth = tree.depth(node2_id)
    distance = node1_depth + node2_depth - 2 * tree.depth(last_ancestor)
    return distance


def dataframe_to_tree(df, id_col, parent_col):
    # Create an instance of the Tree class
    tree = Tree()

    # Create a root node and add it to the tree
    root_id = "Root"
    tree.create_node(root_id, root_id)

    # Iterate through DataFrame rows and add nodes to the tree
    for index, row in df.iterrows():
        node_id = row[id_col]
        parent_id = row[parent_col]

        # Convert NaN parent values to the root node ID
        if pd.isna(parent_id):
            parent_id = root_id

        # Add the current row as a node to the tree
        tree.create_node(tag=node_id, identifier=node_id, parent=parent_id, data=row.drop([id_col, parent_col]))

    # sET VALUES FOR ROOT
    root = tree.get_node(tree.root)
    root.data = {
        'code_article': '/',
        'nom_article': '/',
        'qty': 1,
        }
    return tree


def parse_qty(df, tree):
    """
    Parse the quantity of each article in the tree
    """
    root = tree.get_node(tree.root)
    root.data['effective_qty'] = 1

    # ADD EFFECTIVE QUANTITY
    # The quantity of each product is multiplied by the quantity of the parent in a recursive way
    all_nodes = level_order_traversal(tree)
    for node_id in all_nodes[1:]:
        node = tree.get_node(node_id)
        parent = tree.parent(node_id)
        node.data['effective_qty'] = parent.data['effective_qty'] * node.data['qty']
        df.loc[df['id'] == node_id, 'effective_qty'] = node.data['effective_qty']

    # CALCULATE TOTAL QUANTITY
    #      For a given code article calculate the total quantity of the article
    # As data are not correclty returned from AX, xome articles are doubled, so what we
    # are going to do is to:
    # - Taking the list of each unique code_article
    # - For each one we calculate the total (sum of effective_qty) taking each article of level 1 separately
    # - We take the max among the subtotals
    #

    def find_level1_parent(tree, node_id):
        node = tree.get_node(node_id)
        if node.identifier == tree.root:
            return None
        parent = tree.parent(node_id)
        if parent.identifier == tree.root:
            return node_id
        elif parent.data['niveau'] == 1:
            return parent.identifier
        else:
            return find_level1_parent(tree, parent.identifier)

    root.data['total_qty'] = 1
    # Get the list of unique code_article
    unique_code_articles = df['code_article'].unique().tolist()
    # get the list of level 1 articles
    level_1_articles = df[df['niveau'] == 1]['id'].tolist()
    for code_article in unique_code_articles:
        # Initialise a dict for the total quantity
        qty_by_level = {level1: 0 for level1 in level_1_articles}
        # Get the list of all the articles with the same code_article
        same_code_articles = df[df['code_article'] == code_article]

        for _, article_instance in same_code_articles.iterrows():
            # Get the list of all the articles with the same code_article and level 1
            level1_parent = find_level1_parent(tree, article_instance['id'])
            qty_by_level[level1_parent] += article_instance['effective_qty']

        # Get the max among the subtotals
        max_qty = max(qty_by_level.values())
        # Set the total quantity for each article with the same code_article
        df.loc[same_code_articles.index, 'total_qty'] = max_qty
        #     Update the tree
        for _, article_instance in same_code_articles.iterrows():
            node = tree.get_node(article_instance['id'])
            node.data['total_qty'] = max_qty



    return df, tree

def explose_project(project_code):
    """Generate a dataframe with all the articles associated to a project"""
    # Use a parameterized query to avoid SQL injection
    query = """
           WITH decompose_article AS
(
SELECT
	b.BOMID AS CODE_FORMULE_NOMENCLATURE,
	bv.BOMID AS CODE_FORMULE_PRODUIT,
	b.ITEMID AS CODE_ARTICLE_PRODUIT,
	b.BOMQTY AS QTY,
	b.CREATEDDATETIME ,
	b.CREATEDBY,
	b.RECID,
	b.[PARTITION] ,
	b.DATAAREAID ,
	b.CONFIGGROUPID,
	bv.FROMDATE,
	bv.TODATE,
	bv.ACTIVE
FROM
	AXPROD.dbo.BOM b
LEFT JOIN AXPROD.dbo.BOMVERSION bv 
ON
	b.ITEMID = bv.ITEMID
	AND b.[PARTITION] = bv.[PARTITION]
	AND b.DATAAREAID = bv.DATAAREAID
	AND b.CREATEDDATETIME > bv.FROMDATE
	AND (b.CREATEDDATETIME < bv.TODATE
		OR (bv.TODATE < '01/01/1910'
			AND bv.ACTIVE = 1))
	AND (b.INVENTDIMID NOT LIKE '--R-%' OR b.INVENTDIMID = bv.INVENTDIMID)
),
RecursiveCTE AS (
SELECT 
	NEWID() AS random_id,
    CAST(NULL AS uniqueidentifier) AS parent_id,
	s.ITEMID AS code_article,
	bv.BOMID AS CODE_FORMULE_PRODUIT,
	CAST(NULL AS NVARCHAR(20)) AS CODE_FORMULE_PARENT,
	s.[PARTITION] ,
	S.DATAAREAID ,
	CAST(1 AS numeric) AS QTY,
	1 AS niveau
FROM
	AXPROD.dbo.SALESLINE s
LEFT JOIN AXPROD.dbo.BOMVERSION bv 
	ON 
	S.[PARTITION] = bv.[PARTITION]
	AND bv.DATAAREAID = S.DATAAREAID
	AND s.ITEMID = bv.ITEMID
	AND (
			(
	            s.CREATEDDATETIME > bv.FROMDATE
	            AND (s.CREATEDDATETIME < bv.TODATE OR (bv.TODATE < '01/01/1910' AND bv.ACTIVE = 1))
	            AND s.ITEMBOMID=''
	        )
	    	OR (s.ITEMBOMID = bv.BOMID)
	    )
	AND (s.INVENTDIMID NOT LIKE '--R-%' OR NOT s.ITEMBOMID='' OR s.INVENTDIMID = bv.INVENTDIMID)
WHERE
	PROJID = ?
	AND OMSPROJSETTLENUM = ?
	 AND OMSINVENTTRANSIDSUBFATHER = ''
UNION ALL
-- Seleziona gli articoli associati alle nomenclature contenute nei livelli precedenti
SELECT
	NEWID() AS random_id,
    RC.random_id AS parent_id,
	D.CODE_ARTICLE_PRODUIT AS CODE_ARTICLE,
	D.CODE_FORMULE_PRODUIT AS CODE_FORMULE_PRODUIT,
	CAST(D.CODE_FORMULE_NOMENCLATURE AS NVARCHAR(20)) AS CODE_FORMULE_PARENT,
	D.[PARTITION] ,
	D.DATAAREAID ,
	CAST(D.QTY AS NUMERIC),
	RC.NIVEAU + 1
FROM
	decompose_article D
INNER JOIN
        RecursiveCTE AS RC 
        ON
	RC.CODE_FORMULE_PRODUIT = D.CODE_FORMULE_NOMENCLATURE
	AND RC.[PARTITION] = D.[PARTITION]
	AND D.DATAAREAID = RC.DATAAREAID
WHERE
	RC.NIVEAU < 11
)
SELECT
    RC.random_id AS id,
    RC.parent_id,
	RC.code_article,
	a.NAME AS nom_article,
	RC.CODE_FORMULE_PARENT,
	RC.CODE_FORMULE_PRODUIT,
	RC.QTY,
	niveau
FROM
	RecursiveCTE AS RC
LEFT JOIN Entrepot_Production_V2.dbo.ARTICLE a
ON
	rc.code_article = a.CODE_ARTICLE
	AND rc.[PARTITION] = a.[PARTITION]    """

    with Session_ax() as session:
        con = session.connection()
        # Set timeout to 20 seconds
        con.connection.connection.timeout = 120
        df = pd.read_sql_query(query, con=con, params=(project_code.upper()[:8], project_code.upper()[-1]), )
    return df


extract_features_functions = dict()


# Create a decorator for registering extract_features functions
def extract_features(func):
    extract_features_functions[func.__name__] = func
    return func


# Make new error FeatureNotFound with attribute feature_name
class FeatureNotFound(Exception):
    def __init__(self, feature_name):
        super().__init__(f'Feature {feature_name} not found')
        self.feature_name = feature_name


def build_tree(project_code, filterADV=True):
    # Fetch the list of articles
    logger.debug(f'Fetching data for project {project_code}')
    df = explose_project(project_code)
    logger.debug(f'Fetched {len(df)} rows. Building tree')
    # Some parsing
    df['nom_article'].fillna('', inplace=True)
    df['code_article'].fillna('', inplace=True)
    df['code_article'] = df['code_article'].str.upper()
    df['qty'] = df['QTY'].astype(int)
    df.drop(columns=['QTY'], inplace=True)
    df.sort_values(by='niveau', inplace=True)

    if len((set(df['parent_id']) - set(df['id']))) > 1:
        raise RuntimeError(f"Multiple roots ({len((set(df['parent_id']) - set(df['id'])))}) found in project {project_code}")
    df.drop_duplicates(subset=['id'], keep='first', inplace=True)
    # Build the tree
    tree = dataframe_to_tree(df, id_col='id', parent_col='parent_id')

    # Parse the quantity of each article in the tree
    df, tree = parse_qty(df, tree)

    if not filterADV:
        return tree

    # Get all the children of root
    root_children = tree.children(tree.root)
    adv_children = [c for c in root_children if c.data.code_article.startswith('ADV') and not c.data.code_article.startswith('ADV-TRANSPORT') and not c.data.code_article.startswith('ADV-STRAITANCE') and not c.data.code_article.startswith('ADV-MANUT') and not c.data.code_article.startswith('ADV-NEGOCE') and not c.data.code_article.startswith('ADV-EL-CAB') and not c.data.code_article.startswith('ADV-TRANSFERT')]
    if len(adv_children) > 1:
        raise RuntimeError(f"Multiple ADV articles ({len(adv_children)}) found in project {project_code}")
    elif len(adv_children) == 1:
        # Remove the other children
        for c in root_children:
            if c != adv_children[0]:
                tree.remove_node(c.identifier)
                # Remove from dataframe all the rows that are not in the pruned tree
                all_tree_ids = [n.identifier for n in tree.all_nodes()]
                df = df[df['id'].isin(all_tree_ids)]

    logger.debug(f'Tree built. Extracting features')

    return df, tree

def extract_all_features(project_code):
    df, tree = build_tree(project_code)
    # If there is an ADV article at the second level, it keeps only it

    # Convert to json and save as a file named as the code equipment
    json_tree = convert_tree_to_json_list_info(tree)
    # Dumps as file
    with open(f'./temp/{project_code}_aslistinfo.json', 'w') as f:
        f.write(json.dumps(json_tree, indent=4))

    all_features = dict()

    for feature, func in extract_features_functions.items():
        try:
            all_features.update(func(df, tree))
        except Exception as e:
            logger.error(f'Feature {feature} not found in project {project_code}\n{e}\n{traceback.format_exc()}')
    return all_features


import json
from treelib import Node, Tree


def convert_tree_to_json(tree):
    def process_node(node):
        # Extract relevant data from the node
        if node.data is None:
            code_article = ''
            nom_article = ''
        else:
            code_article = node.data['code_article']
            nom_article = node.data['nom_article']
        # Format the key
        key = f"{code_article} ({nom_article})"
        # Initialize an empty dict for child nodes
        children = { }
        # Process each child node
        for child in tree.children(node.identifier):
            child_id = child.identifier
            child = tree[child_id]
            children.update(process_node(child))
        return {
            key: children
            }

    # Assuming the tree has a single root, start processing from there
    root = tree.get_node(tree.root)
    return process_node(root)


def convert_tree_to_json_list(tree):
    def process_node(node):
        # Extract relevant data from the node
        if node.data is None:
            code_article = ''
            nom_article = ''
        else:
            code_article = node.data['code_article']
            nom_article = node.data['nom_article']
        # Format the key
        key = f"{code_article} ({nom_article})"

        children = tree.children(node.identifier)

        if not children:
            # If the node has no children, return the key directly
            return key
        else:
            # If the node has children, process each child and add to a list
            child_list = [process_node(child) for child in children]
            return {
                key: child_list
                }

    # Assuming the tree has a single root, start processing from there
    root = tree.get_node(tree.root)
    return process_node(root)


def convert_tree_to_json_list_info(tree):
    def process_node(node):
        # Extract relevant data from the node
        if node.data is None:
            data = { }
        else:
            data = dict(node.data)

        # Format the key
        data['id'] = node.identifier
        data["children"] = []

        children = tree.children(node.identifier)
        if not children:
            # If the node has no children, return the key directly
            return data
        else:
            # If the node has children, process each child and add to a list
            child_list = [process_node(child) for child in children]
            data["children"] = child_list
            return data

    # Assuming the tree has a single root, start processing from there
    root = tree.get_node(tree.root)
    return process_node(root)


def add_spec_stmt(code_equip, nom_spec, value):
    stmt = insert(SpecEquipM).values(code_equip=code_equip, nom_spec=nom_spec, value=value).on_conflict_do_update(constraint='spec_equip_un', set_={
        'code_equip': code_equip,
        'nom_spec': nom_spec,
        'value': value,
        'date_modification': datetime.now()
        })
    return stmt


# ================================================================
# ================================================================
# FEATURE EXTRACTION FUNCTIONS
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ================================================================
@extract_features
def extract_powers(df, tree):
    def extract_engine_features(node):
        engines_features = dict()
        engines_features['code_article'] = node.data.code_article
        desc = node.data.nom_article.upper()
        engines_features['description'] = desc
        engines_features['puissance_kw'] = float(re.search(r'MOT.*?(\d+[.,]\d+)KW', desc).group(1))
        return engines_features

    def extract_fan_features(node):
        fan_features = dict()
        fan_features['code_article'] = node.data.code_article
        desc = node.data.nom_article.upper()
        fan_features['description'] = desc
        return fan_features

    def extract_poulie_features(node):
        poulie_features = dict()
        poulie_features['code_article'] = node.data.code_article
        desc = node.data.nom_article.upper()
        poulie_features['description'] = desc
        poulie_features['diametre_mm'] = int(re.search(r'POULIE.*?D([\d]+)', desc).group(1))
        return poulie_features

    features = dict()
    # ALL ENGINES
    # All engne are extracted, power is parsed and they are associated to extraction or soufflage
    engines = df[df['code_article'].str.match('.*') & df['nom_article'].str.match('.*MOT.*\d+KW.*')]
    if engines.empty:
        logger.error('No row found matching criteria for moteurs')
        raise FeatureNotFound('puissance moteurs')
    engines = engines['id'].values.tolist()
    # Retrieve only leaf nodes of moteurs
    for m in engines[::-1]:
        for m2 in engines[::-1]:
            if tree.is_ancestor(m, m2) and m != m2:
                engines.remove(m)
                break
    engines_features = { id: extract_engine_features(tree.get_node(id)) for id in engines }
    # Sort engines by power so that the first one is the most powerful for each group
    engines.sort(key=lambda x: engines_features[x]['puissance_kw'], reverse=True)

    # ALL FANS
    # All fans are extracted and they are associated to extraction or soufflage
    fans = df[df['nom_article'].str.match('.*VENT.*CENT')]
    if fans.empty:
        logger.error('No row found matching criteria for ventilateurs')
        raise FeatureNotFound('ventilateurs')
    fans = fans['id'].values.tolist()
    # Retrieve only leaf nodes of ventilateurs
    for f in fans[::-1]:
        for f2 in fans[::-1]:
            if tree.is_ancestor(f, f2) and f != f2:
                fans.remove(f)
                break
    fans_features = { id: extract_fan_features(tree.get_node(id)) for id in fans }

    # POULIES
    # Here is a little bit more complicated, because poulies have to be associated in pairs
    poulies = df[df['code_article'].str.match('.*') & df['nom_article'].str.match('.*POULIE.*D[\d]')]
    if poulies.empty:
        logger.error('No row found matching criteria for poulies')
        raise FeatureNotFound('poulies')
    poulies = poulies['id'].values.tolist()
    # Retrieve only leaf nodes of poulies
    for p in poulies[::-1]:
        for p2 in poulies[::-1]:
            if tree.is_ancestor(p, p2) and p != p2:
                poulies.remove(p)
                break
    poulies_features = { id: extract_poulie_features(tree.get_node(id)) for id in poulies }
    # Sort poulies by diameter so that the first one is the smallest (engine) for each pair
    poulies.sort(key=lambda x: poulies_features[x]['diametre_mm'])
    # Extract pairs of poulies looking at the distance in the articles tree
    poulies_pairs = list()
    poulies_to_pairs = poulies.copy()
    while len(poulies_to_pairs) > 1:
        # Start from the beginning of the list, so the first element of each couple is the smallest
        # and so it corresponds to the engine poulie
        p = poulies_to_pairs.pop(0)
        nearest_poulie = None
        min_dist = 100000
        # Find the nearest poulie to the current one and remove it from the list
        for p2 in poulies_to_pairs:
            dist = find_distance(tree, p, p2)
            if dist < min_dist:
                nearest_poulie = p2
                min_dist = dist
        poulies_pairs.append((p, nearest_poulie))
        poulies_to_pairs.remove(nearest_poulie)

    # Sort the poulies in the same order as the engines using the tree distance
    if len(poulies_pairs) != len(engines):
        logger.error('Number of poulies pairs different from number of engines')
    else:
        poulies_to_sort = poulies_pairs.copy()
        poulies_pairs = list()
        for e in engines:
            nearest_poulie = None
            min_dist = 100000
            for p in poulies_to_sort:
                dist = find_distance(tree, e, p[0])
                if dist < min_dist:
                    nearest_poulie = p
                    min_dist = dist
            poulies_pairs.append(nearest_poulie)
            poulies_to_sort.remove(nearest_poulie)

    # GROUPE EXTRACTION
    groupe_ext = df[df['code_article'].str.match('.*') & df['nom_article'].str.match('.*GROUPE.*EXT.*')].sort_values(by='niveau').head(1)
    if groupe_ext.empty:
        logger.error('No row found matching criteria for groupe extraction')
        raise FeatureNotFound('puissance moteurs')
    groupe_ext = groupe_ext['id'].values[0]
    engines_ext = [m for m in engines if tree.is_ancestor(groupe_ext, m)]
    fans_ext = [f for f in fans if tree.is_ancestor(groupe_ext, f)]
    poulies_ext = [pair for pair in poulies_pairs if tree.is_ancestor(groupe_ext, pair[0])]

    # Add features for each engine in groupe_ext
    for i, m in enumerate(engines_ext):
        for key, value in engines_features[m].items():
            new_key = f"moteur_ext_{i + 1}_{key}" if i > 0 else f"moteur_ext_{key}"
            features[new_key] = value
    # Add features for each fan in groupe_ext
    for i, f in enumerate(fans_ext):
        for key, value in fans_features[f].items():
            new_key = f"vent_ext_{i + 1}_{key}" if i > 0 else f"vent_ext_{key}"
            features[new_key] = value
    # Add features for each poulie in groupe_ext
    for i, pair in enumerate(poulies_ext):
        # Poulie motrice
        for key, value in poulies_features[pair[0]].items():
            new_key = f"poulie_mot_ext_{i + 1}_{key}" if i > 0 else f"poulie_mot_ext_{key}"
            features[new_key] = value
        # Poulie ventilo
        for key, value in poulies_features[pair[1]].items():
            new_key = f"poulie_vent_ext_{i + 1}_{key}" if i > 0 else f"poulie_vent_ext_{key}"
            features[new_key] = value

    # GROUPE SOUFFLAGE
    groupe_souf = df[df['code_article'].str.match('.*') & df['nom_article'].str.match('.*GROUPE.*V\.AIR.*')].sort_values(by='niveau').head(1)
    if groupe_souf.empty:
        logger.error('No row found matching criteria for groupe soufflage')
        raise FeatureNotFound('puissance moteurs')
    groupe_souf = groupe_souf['id'].values[0]
    engines_souf = [m for m in engines if tree.is_ancestor(groupe_souf, m)]
    fans_souf = [f for f in fans if tree.is_ancestor(groupe_souf, f)]
    poulies_souf = [pair for pair in poulies_pairs if tree.is_ancestor(groupe_souf, pair[0])]

    # Add features for each engine in groupe_souf
    for i, m in enumerate(engines_souf):
        for key, value in engines_features[m].items():
            new_key = f"moteur_souf_{i + 1}_{key}" if i > 0 else f"moteur_souf_{key}"
            features[new_key] = value

    # Add features for each fan in groupe_souf
    for i, f in enumerate(fans_souf):
        for key, value in fans_features[f].items():
            new_key = f"vent_souf_{i + 1}_{key}" if i > 0 else f"vent_souf_{key}"
            features[new_key] = value

    # Add features for each poulie in groupe_souf
    for i, pair in enumerate(poulies_souf):
        # Poulie motrice
        for key, value in poulies_features[pair[0]].items():
            new_key = f"poulie_mot_souf_{i + 1}_{key}" if i > 0 else f"poulie_mot_souf_{key}"
            features[new_key] = value
        # Poulie ventilo
        for key, value in poulies_features[pair[1]].items():
            new_key = f"poulie_vent_souf_{i + 1}_{key}" if i > 0 else f"poulie_vent_souf_{key}"
            features[new_key] = value

    return features


@extract_features
def extract_armoire(df, tree):
    rows = df[df['nom_article'].str.match('ARM.*ELEC.*') & ~(df['nom_article'].str.match('.*COFFRE.*')).fillna(False)]
    armoires = rows['id'].values.tolist()
    # Retrieve only leaf nodes of moteurs
    for m in armoires[::-1]:
        for m2 in armoires[::-1]:
            if tree.is_ancestor(m, m2) and m != m2:
                armoires.remove(m)
                break

    return {
        'code_armoire': tree.get_node(armoires[0]).data.code_article,
        'description_armoire': tree.get_node(armoires[0]).data.nom_article
        }


@extract_features
def has_hygro_option(df, tree):
    rows = df[df['nom_article'].str.match('OPTION HYGRO.*')]
    return {
        'hygro_option': not rows.empty
        }


@extract_features
def has_eco_option(df, tree):
    rows = df[df['nom_article'].str.match('.*PACK ECO.*')]
    return {
        'eco_option': not rows.empty
        }


@extract_features
def extract_code_ADV(df, tree):
    rows = df[df['code_article'].str.match('ADV.*')]
    if rows.empty:
        logger.error('No row found matching criteria for ADV')
        return {
            'code_ADV': None
            }
    return {
        'code_ADV': rows['code_article'].values[0]
        }


@extract_features
def extract_enceinte(df, tree):
    def parse_enceinte(desc: str) -> dict:
        def str_to_cm(s: str) -> float:
            f = float(s.replace(',', '.')) if s else None
            # If the dimensions are in m, convert them to cm
            f = f if f > 80 else f * 100
            # If the dimensions are in mm, convert them to cm
            f = f if f < 2000 else f / 10
            return f

        features = dict()
        # Extract size
        pattern = r'(\d+)[X|L](\d+)[\sA-Z]*HT?(\d+)'
        matches = re.search(pattern, desc)
        if not matches or len(matches.groups()) != 3:
            logger.error(f'Error in extracting dimensions from {desc}')
        else:
            features['longueur_cm'] = str_to_cm(matches.group(1))
            features['profondeur_cm'] = str_to_cm(matches.group(2))
            features['hauteur_cm'] = str_to_cm(matches.group(3))

        # Extract machinerie
        pattern = r'\s((TOIT)|(ARR)|(LAT))($|\s)'
        matches = re.search(pattern, desc)
        if not matches:
            logger.error(f'Error in extracting machinerie from {desc}')
        else:
            features['machinerie'] = matches.group(1).strip()

        # Extract Tunnel
        pattern = r'\s(TUNNEL)($|\s)'
        matches = re.search(pattern, desc)
        features['tunnel'] = bool(matches)
        features['description_enceinte'] = desc
        return features

    row = df[df['nom_article'].str.match('ENC.*X.*H.*')].head(1)
    if row.empty:
        logger.error('No row found matching criteria for extracting enceinte with dimensions')
        row = df[df['nom_article'].str.match('ENC.*')].head(1)
        if row.empty:
            logger.error('No row found matching criteria for extracting enceinte')
            raise FeatureNotFound('dimensions enceinte')
    desc = row['nom_article'].values[0]
    features = parse_enceinte(desc)
    return features


# ^ Add new feature extraction functions here
# Use the following syntax:
#
# @extract_features
# def extract_feature_name(df, tree):
#     # Do stuff
#     return {'feature_name1': feature_value1, 'feature_name2': feature_value2}

# ================================================================
# ================================================================


def process_equip(code_equip):
    logger.debug(f'Processing {code_equip}')
    try:
        features = extract_all_features(code_equip)
    except Exception as e:
        logger.error(f'Error while extracting features for {code_equip}: {e}')
        features = dict(error=True)
    logger.debug(f'Features extracted: {features}')
    stmts = [add_spec_stmt(code_equip, feature, value) for feature, value in features.items()]
    with Session() as session:
        for stmt in stmts:
            session.execute(stmt)
        session.commit()


def get_list_all_af():
    raw_sql = """
    SELECT 
    codeequipment 
    FROM 
    Entrepot_Divalto.dbo.equipement
    WHERE installationDate > '2014-01-01'
    AND codeequipment LIKE 'AF%'
    """
    with Session_ax() as session:
        list_equips = [r[0] for r in session.execute(raw_sql).fetchall()]
    return list_equips


def main():
    import traceback

    # list_equips = get_equips()
    list_equips = get_list_all_af()
    for equip in tqdm(list_equips):
        try:
            process_equip(equip)
        except Exception as e:
            logger.error(f'Error while processing {equip}: {e}\n{traceback.format_exc()}')


if __name__ == "__main__":
    # generate_views_and_procedures()
    project_code = 'AF003678-C'

    process_equip(project_code)  # main()
