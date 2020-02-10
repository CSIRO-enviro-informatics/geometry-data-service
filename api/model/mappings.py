
class DatasetMappings():
   DATASET_RESOURCE_BASE_URI_LOOKUP = {
        "asgs16_sa1": "http://linked.data.gov.au/dataset/asgs2016/statisticalarealevel1",
        "asgs16_sa2": "http://linked.data.gov.au/dataset/asgs2016/statisticalarealevel2",
        "asgs16_sa3": "http://linked.data.gov.au/dataset/asgs2016/statisticalarealevel3",
        "asgs16_sa4": "http://linked.data.gov.au/dataset/asgs2016/statisticalarealevel4",
        "asgs16_mb": "http://linked.data.gov.au/dataset/asgs2016/meshblock",
        "asgs16_ste": "http://linked.data.gov.au/dataset/asgs2016/stateorterritory",
        "asgs16_sua": "http://linked.data.gov.au/dataset/asgs2016/significanturbanarea",
        "asgs16_ireg": "http://linked.data.gov.au/dataset/asgs2016/indigenousregion",
        "asgs16_iloc": "http://linked.data.gov.au/dataset/asgs2016/indigenouslocation",
        "asgs16_iare": "http://linked.data.gov.au/dataset/asgs2016/indigenousarea",
        "asgs16_ra": "http://linked.data.gov.au/dataset/asgs2016/remotenessarea",
        "asgs16_gccsa": "http://linked.data.gov.au/dataset/asgs2016/greatercapitalcitystatisticalarea",
        "asgs16_ucl": "http://linked.data.gov.au/dataset/asgs2016/urbancentreandlocality",
        "asgs16_sosr": "http://linked.data.gov.au/dataset/asgs2016/sectionofstaterange",
        "asgs16_sos": "http://linked.data.gov.au/dataset/asgs2016/sectionofstate",
        "asgs16_ced": "http://linked.data.gov.au/dataset/asgs2016/localgovernmentarea",
        "asgs16_lga": "http://linked.data.gov.au/dataset/asgs2016/commonwealthelectoraldivision",
        "asgs16_nrmr": "http://linked.data.gov.au/dataset/asgs2016/statesuburb",
        "asgs16_ssc": "http://linked.data.gov.au/dataset/asgs2016/naturalresourcemanagementregion",
        "geofabric2_1_1_ahgfcontractedcatchment": "http://linked.data.gov.au/dataset/geofabric/contractedcatchment",
        "geofabric2_1_1_riverregion": "http://linked.data.gov.au/dataset/geofabric/riverregion",
        "geofabric2_1_1_awradrainagedivision": "http://linked.data.gov.au/dataset/geofabric/drainagedivision"
    }
   @classmethod
   def find_resource_uri(cls, dataset_type, dataset_local_id):
        prefix = cls.DATASET_RESOURCE_BASE_URI_LOOKUP.get(dataset_type)
        if prefix is None:
            return None
        return "{0}/{1}".format(prefix, dataset_local_id)

