from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    LargeBinary,
    MetaData,
    ForeignKey,
    Float,
    Date,
    ForeignKey,
    Enum,
    DateTime,
    Boolean,
    UniqueConstraint)
from sqlalchemy.orm import relationship, backref
from src.db_utils.base import BaseAx, engine_ax, ReprTable



class Equip_ax(BaseAx, ReprTable):
    __tablename__ = 'EC_Equipement'

    #id = Column(Integer, primary_key=True)
    customeraddress_ID = Column(Integer)
    codeequipment = Column(String, primary_key=True)
    serialNumber = Column(String)
    CodeType = Column(String)
    Type = Column(String)
    description = Column(String)
    DateInstal = Column(String)
    DateMiseEnService = Column(String)
    baseuser_ID_favoriteTechnician = Column(String)
    DateFinGarantie = Column(String)
    equipment_ID = Column(String)

    def __repr__(self):
        return self._repr(code_equip=self.codeequipment,
                          adressID=self.customeraddress_ID,
                          description=self.description)


class Site_ax(BaseAx, ReprTable):
    __tablename__ = 'EC_Site'

    CodeClient = Column(String)
    CodePostal = Column(String)
    Ville = Column(String)
    Pays = Column(String)
    customerAddress_id = Column(Integer)
    CodeSite = Column(String, primary_key=True)
    AddresseSite = Column(String)
    gpsLongitude = Column(String)
    gpsLatitude = Column(String)

    def __repr__(self):
        return self._repr(code_client=self.CodeClient,
                          code_site=self.CodeSite,
                          ville=self.Ville)



class Client_ax(BaseAx, ReprTable):
    __tablename__ = 'EC_Client'

    CodeClient = Column(String, primary_key=True)
    RaisonSociale = Column(String)
    Addresse = Column(String)
    CodePostal = Column(String)
    Ville = Column(String)
    Pays = Column(String)
    Telephone = Column(String)
    Email = Column(String)
    CodeSegment = Column(String)
    LabelSegment = Column(String)
    CodeGroupe = Column(String)
    LabelGroupe = Column(String)

    def __repr__(self):
        return self._repr(code_client=self.CodeClient,
                          raison_sociale=self.RaisonSociale,
                          code_postal=self.CodePostal)



class ClientCommandes_ax(BaseAx, ReprTable):
    """Liste des AF + info Client directement de Ax (à jour)"""
    __tablename__ = 'ClientsCommandesSynthese'


    CodeCdeClts = Column(String, primary_key=True)
    NomCde = Column(String)
    CodeCltLiv = Column(String)
    CodeProj = Column(String)
    NomLiv = Column(String)
    NomAdLiv = Column(String)


    def __repr__(self):
        return self._repr(CodeCdeClts=self.CodeCdeClts,
                          NomCde=self.NomCde,
                          CodeCltLiv=self.CodeCltLiv,
                          CodeProj=self.CodeProj,
                          NomAdLiv=self.NomAdLiv)





class CarnetAdresses_ax(BaseAx, ReprTable):
    """Liste des codes livraison directement de Ax (à jour)"""
    __tablename__ = 'CarnetAdresses'

    CodeClt = Column(String)
    NomAdr = Column(String)
    Cp = Column(String)
    Ville = Column(String)
    Pays = Column(String)

    CodeAdr = Column(String, primary_key=True)
    Rue = Column(String)


    def __repr__(self):
        return self._repr(CodeClt=self.CodeClt,
                          NomAdr=self.NomAdr,
                          CodeAdr=self.CodeAdr)


class ProjetArticle_ax(BaseAx, ReprTable):
    """Tableau avec les sous-ensembles de AX"""
    __tablename__ = 'ProjetDdesArticles'

    NomProjet = Column(String, primary_key=True)
    CodeCde = Column(String)
    CodeProjet = Column(String)
    NomProduit = Column(String)
    Ensemble = Column(String)
    SousEnsemble = Column(String)


    def __repr__(self):
        return self._repr(CodeProjet=self.CodeProjet,
                          NomProduit=self.NomProduit,
                          Ensemble=self.Ensemble,
                          SousEnsemble=self.SousEnsemble)


class NewEquip_ax(BaseAx, ReprTable):
    """Tableau avec les sous-ensembles de AX"""
    __tablename__ = 'EC_New_Equipment'

    SerialNumber = Column(String, primary_key=True)
    NomProduit = Column(String)
    Type = Column(String)
    CodeClient = Column(String)
    name = Column(String)
    CodeAdr = Column(String)
    Rue = Column(String)
    Cp = Column(String)
    Ville = Column(String)
    Pays  = Column(String)
    NumOrganisation = Column(String)


    def __repr__(self):
        return self._repr(SerialNumber=self.SerialNumber,
                          NomProduit=self.NomProduit,
                          name=self.name)

class AXConfiguration_ax(BaseAx, ReprTable):
    """Tableau avec les configurations des routeurs à partir de la nomenclature des armoires"""
    __tablename__ = 'EC_Configuration'

    CodeArmoire = Column(String, primary_key=True)
    Equipement = Column(String)
    ConnexionClient = Column(String)
    Config = Column(String)
    VersionConfig = Column(String)
    EquipementConnecte1 = Column(String)
    EquipementConnecte2 = Column(String)
    EquipementConnecte3 = Column(String)
    EquipementConnecte4 = Column(String)
    EquipementConnecte5  = Column(String)

    def __repr__(self):
        return self._repr(CodeArmoire=self.CodeArmoire,
                          TypeConfig=self.Config,
                          EquipementConnecte1=self.EquipementConnecte1)