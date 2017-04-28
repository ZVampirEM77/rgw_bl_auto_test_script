import os
import argparse
import subprocess

def exec_command(command):
    p = subprocess.Popen(command, shell=True, stderr=subprocess.STDOUT)
    p.communicate()
    

def exec_command_with_return(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

def ParseCommandLine():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ceph-path', action = 'store', dest = 'ceph_path', default = '')
    result = parser.parse_args()
    return result

if __name__ == '__main__':
    cmd_line_param = ParseCommandLine()
    ceph_path = cmd_line_param.ceph_path
    if ceph_path == "":
        print "You must specify value for --ceph-path which is 'build' dir for version later than K version or 'src' dir for version earlier than K verison"
    else:
        current_path = os.getcwd()
        os.chdir(ceph_path)
        exec_command('./radosgw-admin -c ceph.conf user create --uid=bl_deliver --access-key=bl_deliver --secret-key=bl_deliver --display-name="Bucket Logging Delivery" --bl_deliver')
        exec_command('./radosgw-admin -c ceph.conf realm create --rgw-realm=default --default')
        exec_command('./radosgw-admin -c ceph.conf zonegroup modify --rgw-zonegroup=default --master')
        exec_command('./radosgw-admin -c ceph.conf zone modify --access-key=bl_deliver --secret=bl_deliver --bl_deliver --rgw-zonegroup=default --rgw-zone=default')
        exec_command('./radosgw-admin -c ceph.conf zone get --rgw-zone=default')
        exec_command('./stop.sh rgw')
        exec_command('/home/enming/BL/ceph/src/.libs/lt-radosgw -c /home/enming/BL/ceph/src/ceph.conf --log-file=/home/enming/BL/ceph/src/out/rgw.log --debug-rgw=20 --debug-ms=1')
        exec_command('./radosgw-admin -c ceph.conf zone get --rgw-zone=default')
        exec_command('./radosgw-admin -c ceph.conf user create --uid=rgw_bl_test --access-key=rgw_bl_test --secret-key=rgw_bl_test --display-name="rgw_bl_test"')
        exec_command('./radosgw-admin -c ceph.conf user create --uid=rgw_bl_test2 --access-key=rgw_bl_test2 --secret-key=rgw_bl_test2 --display-name="rgw_bl_test2"')


        os.chdir(current_path)
        exec_command('s3cmd -c rgw_bl_test.s3cfg mb s3://bl-111')
        exec_command('s3cmd -c rgw_bl_test.s3cfg mb s3://bl-222')
        exec_command('s3cmd -c rgw_bl_test.s3cfg accesslog s3://bl-111 --access-logging-target-prefix=s3://bl-111/log/')
        exec_command('s3cmd -c rgw_bl_test.s3cfg accesslog s3://bl-222 --access-logging-target-prefix=s3://bl-222/log/')
        exec_command('s3cmd -c rgw_bl_test.s3cfg put rgw_bl_test.s3cfg s3://bl-111')

        os.chdir(ceph_path)
        exec_command('./radosgw-admin bl list')
        exec_command('./radosgw-admin bl process')
        exec_command('./radosgw-admin bl list')

        os.chdir(current_path)
        exec_command('s3cmd -c rgw_bl_test.s3cfg ls s3://bl-111')
        exec_command('s3cmd -c rgw_bl_test.s3cfg ls s3://bl-111/log/')

