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

    def reformat_list_into_table(self, switch_name, datetime, output_list):
        _count = 0
        _count_slot_port_avg = 0
        list = output_list
        header1 = []
        header2 = []
        header3 = []
        list_port_slot = []
        list_port_average = []
        list_join_slot_average = []
        for i in list:
            if re.search("\t", i):
                aux = i.replace('\t', "")
                aux = aux.replace('\n', "")
                aux = aux.replace('Total', "")
                aux = re.sub(r'  *', ' ', aux)
                header1.append(aux.split(' ')[1:17])
            if re.search("slot ", i):
                aux = i.replace('slot ', "")
                header2.append(aux.split(":")[0])
            if re.search("slot", i):
                aux = i.replace('slot ', "")
                aux = aux.replace('\n', "")
                aux = re.sub(r'.: *', '', aux)
                aux = re.sub(r'  *', ' ', aux)
                header3.append(aux.split(" ")[0:16])
        for i in header3:
            for e in i:
                if 'k' in e or 'm' in e:
                    list_port_average.append("{};{}".format(e[:-1], e[-1:]))
                else:
                    list_port_average.append("{};b".format(e))
        for i in header2:
            for e in header1:
                for j in e:
                    list_port_slot.append("{}/{}".format(i, j))
                    _count += 1
                if _count == 16:
                    _count = 0
                    del header1[0]
                    break

        for i in list_port_slot:
            for e in list_port_average:
                list_join_slot_average.append("{};{};{};{}".format(datetime, switch_name, i, e))
                _count_slot_port_avg += 1
                if _count_slot_port_avg == 1:
                    _count_slot_port_avg = 0
                    del list_port_average[0]
                    break
        return list_join_slot_average

    def reformat_switchshow_into_table(self, switchshow):
        switchshow_table = []
        count = 0;
        aux_table = []
        for i in switchshow:
            aux = i.replace('switchState:\tOnline   \n', "")
            aux = re.sub(r'\t *', ';', aux)
            aux = re.sub(r'   *', ';', aux)
            aux = re.sub(r'   *', ';', aux)
            aux = re.sub(r' ;', ';', aux)
            aux = re.sub(r' \n', '', aux)
            aux = re.sub(r'\n', '', aux)
            if aux != '':
                aux_table.append(aux.split(";"))
        for i in aux_table:
            if len(i) == 11:
                switchshow_table.append(i[1:])
            else:
                switchshow_table.append(i)
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
    today = datetime.datetime.now()
    date_time = today.strftime("%Y-%m-%d %H:%M:%S")
    output_list = []
    sansw_list = []
    ftp_list = []
    switchshow_table = []
    portshow_table = []
    alias_list = []
    wwn_list = []
    alias_list_aux = []
    report_table = []

    loaded_key = key_load('mykey.key')

    sansw_file = file_decrypt(loaded_key, 'sansw.conf', 'sansw.conf')

    for i in sansw_file.split('\n'):
        if i != '':
            sansw_list.append(i.split(';'))
    for i in sansw_list:
        sansw_name = i[0]
        user = i[1]
        passwd = i[2]
        ip_addr = i[3]
        remote = RemoteClient(ip_addr, user, passwd)
        remote.connection()
        output_list = remote.execute_unix_commands("switchshow | grep -i Online")
        switchshow_table = remote.reformat_switchshow_into_table(output_list)
        for i in switchshow_table:
            slot_port = "{}/{}".format(i[1], i[2])
            portshow_table = remote.execute_unix_commands("portshow {}".format(slot_port))
            wwn_list = remote.get_wwn_from_port(portshow_table)
            for e in wwn_list:
                alias_list_aux = remote.execute_unix_commands("nodefind {} | grep Alias".format(''.join(e)))
                if len(alias_list_aux) != 0:
                    alias_list.append(remote.get_text_from_alias(alias_list_aux))
            report_table.append("{},{},{},{}".format(date_time, sansw_name, ','.join(i), ' '.join(alias_list)))
            alias_list[:] = []
        remote.disconnect()

    remote.create_report_file(report_table)

