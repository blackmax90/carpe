
import os

from modules import manager
from modules import interface
from modules.Googledrive import google_drive_backsync as gs
from dfvfs.lib import definitions as dfvfs_definitions

class GoogledriveentryConnector(interface.ModuleConnector):
    NAME = 'Google_drive_entry_Connector'
    DESCRIPTION = 'Module for Googledrive_Sync_local_entry_info'

    _plugin_classes = {}

    def __init__(self):
        super(GoogledriveentryConnector, self).__init__()

    def Connect(self, par_id, configuration, source_path_spec, knowledge_base):

        this_file_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'schema' + os.sep

        yaml_list = [this_file_path + 'lv1_app_google_drive_snapshot_local_entry.yaml']

        table_list = ['lv1_app_google_drive_snapshot_local_entry']

        if not self.check_table_from_yaml(configuration, yaml_list, table_list):
            return False

        if source_path_spec.parent.type_indicator != dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION:
            par_id = configuration.partition_list['p1']
        else:
            par_id = configuration.partition_list[getattr(source_path_spec.parent, 'location', None)[1:]]

        if par_id is None:
            return False

        users = []
        for user_accounts in knowledge_base._user_accounts.values():
            for hostname in user_accounts.values():
                if hostname.identifier.find('S-1-5-21') == -1:
                    continue
                users.append(hostname.username)

        for user in users:
            user_path = f"/Users/{user}"
            gs_path = f"/AppData/Local/Google/Drive"

            output_path = configuration.root_tmp_path + os.sep + configuration.case_id + os.sep + \
                          configuration.evidence_id + os.sep + par_id

            self.ExtractTargetDirToPath(source_path_spec=source_path_spec,
                                                     configuration=configuration,
                                                     dir_path=user_path + gs_path,
                                                     output_path=output_path)
            try:
                e_data = []
                info = [par_id, configuration.case_id, configuration.evidence_id]
                entry_data = gs.snapshot_local(output_path + os.sep + "Drive" + os.sep + 'user_default' + os.sep)

                for d in entry_data:
                    e_data.append(info + d)

                query = f"INSERT INTO lv1_app_google_drive_snapshot_local_entry values (%s, %s, %s, %s, %s, %s)"

                configuration.cursor.bulk_execute(query, e_data)
            except:
                return False

manager.ModulesManager.RegisterModule(GoogledriveentryConnector)