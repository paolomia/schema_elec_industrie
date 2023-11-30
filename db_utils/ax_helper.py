from src.db_utils.base import Session_ax, Session
from src.db_utils.tables import EquipM, SiteM, ClientM
from src.db_utils.tables_ax import Equip_ax, Site_ax, Client_ax
# Init the logger
from src.log_init import make_logger
logger = make_logger('ax_helper')


# Check des driver microsoft sql
def Test_ax():
    from src.db_utils.base import Session_ax
    try:
        with Session_ax() as session:
            results = session.query()
    except:
        raise RuntimeError("As-tu installé les driver? "
                           "Microsoft® ODBC Driver 11 for SQL Server® - Windows https://www.microsoft.com/fr-fr/download/details.aspx?id=36434"
                           "pour SQL server 2012")
    print("Connexion a Microsoft SQL ok")
    return True





def get_equip_info_divalto(AF: str, strictly_equal:bool = True):
    """Find all equipment with a matching AF in Divalto tables"""
    if strictly_equal:
        equip_criteria = Equip_ax.codeequipment == AF
    else:
        equip_criteria = Equip_ax.codeequipment.like(f'%{AF}%')
    with Session_ax() as session:
        results = session.query(Client_ax, Site_ax, Equip_ax).filter(
            Equip_ax.customeraddress_ID == Site_ax.customerAddress_id,
            Client_ax.CodeClient == Site_ax.CodeClient,
            equip_criteria
        ).all()
    out = []
    for result in results:
        client = ClientM(
            code_client = result[0].CodeClient,
            raison_sociale = result[0].RaisonSociale
        )
        site = SiteM(
            code_client = result[0].CodeClient,
            code_site = result[1].CodeSite,
            code_postal = result[1].CodePostal,
            adresse = result[1].AddresseSite,
            ville = result[1].Ville,
            pays = result[1].Pays,
            lat = result[1].gpsLatitude,
            long = result[1].gpsLongitude
        )
        equip = EquipM(
            code_site = result[1].CodeSite,
            code_equip = result[2].codeequipment,
            type = result[2].Type,
            descr = result[2].description
        )
        out.append((client, site, equip))
    return out


def get_adress_ax(AF: str, strictly_equal:bool = True):
    """Return only adress info using ax table"""
    AF = AF.split("-")[0]
    from src.db_utils.tables_ax import ClientCommandes_ax, CarnetAdresses_ax
    if strictly_equal:
        equip_criteria = ClientCommandes_ax.CodeProj == AF
    else:
        equip_criteria = ClientCommandes_ax.CodeProj.like(f'%{AF}%')
    with Session_ax() as session:
        results = session.query(ClientCommandes_ax, CarnetAdresses_ax).filter(
        ClientCommandes_ax.CodeCltLiv == CarnetAdresses_ax.CodeClt,
        CarnetAdresses_ax.NomAdr == ClientCommandes_ax.NomAdLiv,
        equip_criteria
    ).all()
    result = results[0]

    print(result)
    code_client = result[0].CodeCltLiv
    code_site = result[1].CodeAdr
    # Format code site as code_clientLcode_site

    if "L" not in code_site:
        code_site = code_client + "L" + code_site
    client = ClientM(
        code_client=code_client,
        raison_sociale=result[0].NomCde.title(),
    )
    site = SiteM(
        code_client=code_client,
        code_site=code_site,
        code_postal=result[1].Cp,
        adresse=result[1].Rue,
        ville=result[1].Ville,
        pays=result[1].Pays
    )

    return client, site

def get_client_name_ax(AF: str, strictly_equal:bool = True, force:bool = True):
    """Find all equipment with a matching AF in AX tables"""
    from src.db_utils.tables_ax import ClientCommandes_ax, CarnetAdresses_ax, Client_ax

    if strictly_equal:
        equip_criteria = ClientCommandes_ax.CodeProj == AF
    else:
        equip_criteria = ClientCommandes_ax.CodeProj.like(f'%{AF}%')
    with Session_ax() as session:
        result = session.query(ClientCommandes_ax, CarnetAdresses_ax).filter(
        ClientCommandes_ax.CodeCltLiv == CarnetAdresses_ax.CodeClt,
        CarnetAdresses_ax.NomAdr == ClientCommandes_ax.NomAdLiv,
        equip_criteria
    ).first()
    if result is None:
        logger.warning(f"Nom client non trouvé pour AF = {AF}")
    return  result[0].NomCde.title()


def get_equip_info_ax(AF: str, strictly_equal:bool = True, force:bool = True):
    """Find all equipment with a matching AF in AX tables"""
    from src.db_utils.tables_ax import ClientCommandes_ax, CarnetAdresses_ax, Client_ax

    if strictly_equal:
        equip_criteria = ClientCommandes_ax.CodeProj == AF
    else:
        equip_criteria = ClientCommandes_ax.CodeProj.like(f'%{AF}%')
    with Session_ax() as session:
        results = session.query(ClientCommandes_ax, CarnetAdresses_ax).filter(
        ClientCommandes_ax.CodeCltLiv == CarnetAdresses_ax.CodeClt,
        CarnetAdresses_ax.NomAdr == ClientCommandes_ax.NomAdLiv,
        equip_criteria
    ).all()
    out = []
    for result in results:
        # print(result)
        code_client =  result[0].CodeCltLiv
        code_site = result[1].CodeAdr
        # Format code site as code_clientLcode_site

        if "L" not in code_site:
            code_site = code_client + "L" + code_site

        client = ClientM(
            code_client = code_client,
            raison_sociale = result[0].NomCde.title(),
        )
        site = SiteM(
            code_client = code_client,
            code_site = code_site,
            code_postal = result[1].Cp,
            adresse = result[1].Rue,
            ville = result[1].Ville,
            pays = result[1].Pays
        )
        equip = EquipM(
            code_site = code_site,
            code_equip = result[0].CodeProj,
            # TODO: Fix below
            type = "Inconnue",
            descr = None
        )
        out.append((client, site, equip))
    return out


def get_equip_info_newtable(AF: str, strictly_equal:bool = True, force:bool = False):
    """Find all equipment with a matching AF in the new AX table"""
    from src.db_utils.tables_ax import NewEquip_ax

    if strictly_equal:
        equip_criteria = NewEquip_ax.SerialNumber == AF
    else:
        equip_criteria = NewEquip_ax.SerialNumber.like(f'%{AF}%')
    with Session_ax() as session:
        results = session.query(NewEquip_ax).filter(
        equip_criteria
    ).all()
    out = []
    for result in results:
        print(result)

        code_client =  result.CodeClient
        code_site = result.CodeAdr
        if code_site is None:
            if force:
                print("*"*50)
                print("! "* 50 )
                print("Erreur de code adresse, je vais le chercher ailleur mais ça me plait pas du tout :|".upper())
                print("! " * 50)
                print("*" * 50)
                client, site = get_adress_ax(AF, strictly_equal=strictly_equal)
                code_site = site.code_site
            else:
                raise RuntimeError("Erreur dans le code site de livraison. Passer voir l'ADV pour corriger le problème.")
        else:
            client = ClientM(
                code_client = code_client,
                raison_sociale = result.name.title(),
                siren = result.NumOrganisation

            )
            site = SiteM(
                code_client = code_client,
                code_site = code_site,
                code_postal = result.Cp,
                adresse = result.Rue,
                ville = result.Ville,
                pays = result.Pays

            )
        equip = EquipM(
            code_site=code_site,
            code_equip=result.SerialNumber,
            type=result.Type,
            descr=result.NomProduit
        )

        out.append((client, site, equip))

    return out

def get_equip_info(AF: str, strictly_equal:bool = True):
    if strictly_equal:
        equip_criteria = EquipM.code_equip == AF
    else:
        equip_criteria = EquipM.code_equip.like(f'%{AF}%')
    with Session() as session:
        results = session.query(ClientM, SiteM, EquipM).filter(
            EquipM.code_site == SiteM.code_site,
            ClientM.code_client == SiteM.code_client,
            equip_criteria
        ).all()
    return results[0]




def add_from_equip(AF: str, strictly_equal: bool = True, force=False) -> bool:
    """Look for an AF in Microsoft SQL, find client and site associated and add all of them to the database.
    Return True if the operation is successful"""
    # Look in the Microsoft SQL database for the AF code (if contained in any equipment)



    results = get_equip_info_divalto(AF, strictly_equal=strictly_equal)

    #results = get_equip_info_newtable(AF, strictly_equal=strictly_equal, force=force)


    # Return an error if there is not exactly one result
    n_results = len(results)
    if n_results == 0:
        logger.error(f"Pas d'article qui contiennent le code AF `{AF}`")
        raise RuntimeError(f"Pas d'article qui contiennent le code AF `{AF}`")
    elif n_results > 1:
        err_msg = f"Attention, il y a plusieurs articles qui contiennent le code AF `{AF}`, je vais prendre le dernier\n"
        err_msg += "\n".join([str(res) for res in results[:5]])
        if n_results > 5:
            err_msg += f"\n... ({n_results} résultats totals)"
        logger.error(err_msg)
        # raise RuntimeError(err_msg)

    # TODO: Ici je prends par defaut le dernier. Est-ce que c'est bien de faire cela ??
    client, site, equip = results[-1]
    logger.info(f"Équipement trouvé: {results}")
    # Add the equipment to the cabine connectée database

    with Session() as session:
        client_exists = session.query(
            session.query(ClientM).filter(ClientM.code_client == client.code_client).exists()
            ).scalar()
        if client_exists:
            logger.info(f"Le client {client} est déjà enregistré")
        else:
            session.add(client)
        site_exists = session.query(
            session.query(SiteM).filter(SiteM.code_site == site.code_site).exists()
            ).scalar()
        if site_exists:
            logger.info(f"Le site {site} est déjà enregistré")
        else:
            session.add(site)
        equip_exists = session.query(
            session.query(EquipM).filter(EquipM.code_equip == equip.code_equip).exists()
            ).scalar()
        if equip_exists:
            logger.info(f"L'équipement {equip} est déjà enregistré")
        else:
            session.add(equip)
        session.commit()
    return True

# Check du driver AX
# Test_ax()

if __name__ == "__main__":
    found = get_equip_info_ax(AF="3879", strictly_equal=False)
    print(found)



