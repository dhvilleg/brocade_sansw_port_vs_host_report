import paramiko
from paramiko.auth_handler import AuthenticationException, SSHException
import logging
import re
import datetime
from encriptor import key_create, key_write, file_decrypt, key_load, file_encrypt

class RemoteClient:

    def __init__(self, ipaddr, username, password):
        self.ipaddr = ipaddr
        self.username = username
        self.password = password
        self.client = None
        self.conn = None

    def connection(self):
        if self.conn is None:
            try:
                self.client = paramiko.SSHClient()
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                self.client.connect(
                    self.ipaddr,
                    username=self.username,
                    password=self.password,
                    look_for_keys=False
                )

            except AuthenticationException as error:
                logging.error("autenticacion fallida, vuelva a intentar \n error es {}".format(error))
                raise error
        return self.client

    def disconnect(self):
        if self.client:
            self.client.close()

    def execute_unix_commands(self, command):
        self.conn = self.connection()
        stdin, stdout, stderr = self.conn.exec_command(command)
        stdout.channel.recv_exit_status()
        response = stdout.readlines()
        return response



    def reformat_switchshow_into_table(self, switchshow):
        switchshow_table = []
        count = 0;
        aux_table = []
        for i in switchshow:
            #code here fabric ID '"switchshow" on FID {}:'.format(), get variable from function parameter
            aux = i.replace('switchState:\tOnline   \n', "")
            aux = aux.replace('---------------------------------------------------', '')
            aux = aux.replace('"switchshow" on FID 57:', '')
            aux = aux.replace('"switchshow" on FID 58:', '')
            aux = re.sub(r'\t *', ';', aux)
            aux = re.sub(r'   *', ';', aux)
            aux = re.sub(r'   *', ';', aux)
            aux = re.sub(r' ;', ';', aux)
            aux = re.sub(r'^ ', ';', aux)
            aux = re.sub(r'^;', '', aux)
            aux = re.sub(r';$', '', aux)
            aux = re.sub(r' \n', '', aux)
            aux = re.sub(r'\n', '', aux)
            if aux != '':
                switchshow_table.append(aux.split(";"))
        return switchshow_table

    def get_wwn_from_port(self, port_info_list):
        aux_list = []
        wwn_list = []
        p = re.compile(r'(?:[0-9a-fA-F]:?){16}')
        for i in port_info_list:
            aux_list.append(re.findall(p, i))
        for i in aux_list:
            if len(i) > 0:
                wwn_list.append(i)
        return wwn_list

    def get_text_from_alias(self, alias_list):
        if alias_list[0] != '':
            if not re.search("    Aliases:\n", alias_list[0]):
                aux = alias_list[0].replace('    Aliases: ', "")
                aux = aux.replace('\n', "")
                return aux
            else:
                return "None"
        else:
            return "None"

    def create_report_file(self, output_list):
        today = datetime.datetime.now()
        date = today.strftime("%Y-%m-%d")
        f = open("all_san_sw_inventory_{}.csv".format(date), "w+")
        f.write("date,sansw name,index,slot,port,address,media,speed,status,proto,port_type,WWN/ISL/NPIV,hosts\n")
        for i in output_list:
            f.write("{}\n".format(i))
        f.close()


if __name__ == '__main__':
    output_list = []
    sansw_list = []
    ftp_list = []
    switchshow_table = []
    portshow_table = []
    alias_list = []
    wwn_list = []
    alias_list_aux = []
    report_table = []
    slot_port = ""
    text_to_csv = ""

    loaded_key = key_load('mykey.key')

    sansw_file = file_decrypt(loaded_key, 'sansw.conf', 'sansw.conf')

    for i in sansw_file.split('\n'):
        if i != '':
            sansw_list.append(i.split(';'))
    for i in sansw_list:
        today = datetime.datetime.now()
        date_time = today.strftime("%Y-%m-%d %H:%M:%S")
        sansw_name = i[0]
        user = i[1]
        passwd = i[2]
        ip_addr = i[3]
        vendor = i[4]
        sansw_type = i[5]
        virtual_fid = 0
        if len(i) == 7:
            virtual_fid = i[6]

        remote = RemoteClient(ip_addr, user, passwd)
        remote.connection()
        if virtual_fid != 0:
            output_list = remote.execute_unix_commands('fosexec --fid {} -cmd "switchshow | grep -e Online -e No_Light | grep -v switchState | grep -v FCIP"'.format(virtual_fid))
            switchshow_table = remote.reformat_switchshow_into_table(output_list)
            print(switchshow_table)
            for e in switchshow_table:
                if sansw_type == 'SANDIR':
                    slot_port = "{}/{}".format(e[1], e[2])
                    text_to_csv = "{},{},{}".format(date_time, sansw_name, vendor)
                else:
                    slot_port = "{}".format(e[0])
                    text_to_csv = "{},{},{},".format(date_time, sansw_name, vendor)
                portshow_table = remote.execute_unix_commands('fosexec --fid {} -cmd "portshow {}"'.format(virtual_fid, slot_port))
                wwn_list = remote.get_wwn_from_port(portshow_table)
                for g in wwn_list:
                    alias_list_aux = remote.execute_unix_commands('fosexec --fid {} -cmd "nodefind {} | grep Alias"'.format(virtual_fid, ''.join(g)))
                    if len(alias_list_aux) != 0:
                        alias_list.append(remote.get_text_from_alias(alias_list_aux))
                report_table.append("{},{},{}".format(text_to_csv, ','.join(e), ' '.join(alias_list)))
                print("{},{},{}".format(text_to_csv, ','.join(e), ' '.join(alias_list)))
                alias_list[:] = []
            remote.disconnect()
        else:
            output_list = remote.execute_unix_commands("switchshow | grep -e Online -e No_Light | grep -v switchState | grep -v FCIP")
            switchshow_table = remote.reformat_switchshow_into_table(output_list)
            for i in switchshow_table:
                if sansw_type == 'SANDIR':
                    slot_port = "{}/{}".format(i[1], i[2])
                    text_to_csv = "{},{},{}".format(date_time, sansw_name, vendor)
                else:
                    slot_port = "{}".format(i[0])
                    text_to_csv = "{},{},{},".format(date_time, sansw_name, vendor)
                portshow_table = remote.execute_unix_commands("portshow {}".format(slot_port))
                wwn_list = remote.get_wwn_from_port(portshow_table)
                for e in wwn_list:
                    alias_list_aux = remote.execute_unix_commands("nodefind {} | grep Alias".format(''.join(e)))
                    if len(alias_list_aux) != 0:
                        alias_list.append(remote.get_text_from_alias(alias_list_aux))
                report_table.append("{},{},{}".format(text_to_csv, ','.join(i), ' '.join(alias_list)))
                print("{},{},{}".format(text_to_csv, ','.join(i), ' '.join(alias_list)))
                alias_list[:] = []
            remote.disconnect()

    remote.create_report_file(report_table)
