import multiprocessing
import os
from multiprocessing import Queue
from typing import List

import paramiko as paramiko


class SSHExecutor:

    def __init__(self, user,addr,path):
        self.user = user
        self.addr = addr
        self.path = path
        #Executor should not make any connection in init as parameters can be overwritten afterward

    def get_connection(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.addr, username=self.user)
        return ssh

    def exec(self,cmd, terminated_event = None, bin_paths : List[str] = None, queue: Queue = None, options = None, stdin = None, timeout=None):
        if terminated_event is None:
            terminated_event = multiprocessing.Event()
        path_list = [self.path+'/'+p for p in (bin_paths if bin_paths is not None else [])]
        if options and options.show_cmd:
            print("Executing on %s (PATH+=%s) :\n%s" % (self.addr,':'.join(path_list), cmd))

        cmd = 'cd '+ self.path + '\n' + cmd
        if path_list:
          cmd = 'export PATH="%s:$PATH"\n' % (':'.join(path_list)) + cmd
        ssh = self.get_connection()
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd,timeout=timeout, get_pty=True)

        if stdin is not None:
            ssh_stdin.write(stdin)

        out=''
        err=''

        while not terminated_event.is_set() and not ssh_stdout.channel.exit_status_ready():
            terminated_event.wait(1)
        if terminated_event.is_set():
            ssh.close()
        out = ssh_stdout.read().decode()
        err = ssh_stderr.read().decode()
        ret = ssh_stdout.channel.recv_exit_status()
        return os.getpid(),out,err,ret


        #
        # try:
        #     s_output, s_err = [x.decode() for x in
        #                        p.communicate(stdin, timeout=timeout)]
        #     p.stdin.close()
        #     p.stderr.close()
        #     p.stdout.close()
        #     return pid, s_output, s_err, p.returncode
        # except TimeoutExpired:
        #     print("Test expired")
        #     p.terminate()
        #     p.kill()
        #     os.killpg(pgpid, signal.SIGKILL)
        #     os.killpg(pgpid, signal.SIGTERM)
        #     s_output, s_err = [x.decode() for x in p.communicate()]
        #     print(s_output)
        #     print(s_err)
        #     p.stdin.close()
        #     p.stderr.close()
        #     p.stdout.close()
        #     return 0, s_output, s_err, p.returncode
        # except KeyboardInterrupt:
        #     os.killpg(pgpid, signal.SIGKILL)
        #     return -1, s_output, s_err, p.returncode