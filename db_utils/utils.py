from .base import Session


# Récupère la liste des équipements
def get_equips():
    """
    Return a list of all the code_equip
    """
    query = '''SELECT r2e.code_equip
        FROM ftp_user
        INNER JOIN ras_config ON ftp_user.id=ras_config.ftp_id
        INNER JOIN ras ON ras_config.code_config=ras.code_config
        INNER JOIN ras2equip r2e on ras_config.code_ras = r2e.code_ras
        INNER JOIN projet_config ON ras_config.code_ras = projet_config.code_ras
        WHERE projet_config.infrastructure IN ('ovh')'''
    with Session() as session:
        res = session.execute(query)
        res = res.fetchall()
    return [x[0] for x in res]