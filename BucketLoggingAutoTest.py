#-*- coding:utf-8 -*-
'''
python BucketLoggingAutoTest.py --source-bucket=* --uid=* --display-name=* --target-bucket=* --target-prefix=* --opt-type=*
--source-bucket       --   source bucket name
--uid                 --   user id
--display-name        --   user's display name in RGW
--target-bucket       --   target bucket name
--target-prefix       --   bucket log prefix
--ceph-path           --   ceph path
--opt-type            --   * get_id       --   get user id and display name
                           * run_func_test --   enable/disable BL test
                           * run_usage_test --   usage scenario test
                           * run_rgw_test   --   RGW Related Test

author:    Enming Zhang
date:      2017/04/26
version:   0.1
'''

import os
import time
import argparse
import requests
import subprocess
from awsauth import S3Auth

s3_user_authv2 = S3Auth('bl_test', 'bl_test', 'http:127.0.0.1:8000')
s3_cfg = 'bl_test.s3cfg'
s3_cfg_2 = 'bl_test_2.s3cfg'
req_headers = {'Content-Type': 'text/xml'}

def exec_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()
    
def exec_command_with_return(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

def ok_display(content):
    return "[\033[1;;32m%s\033[0m]" % (content)

def fail_display(content):
    return "[\033[1;;41m%s\033[0m]" % (content)


class ReqXml(object):
    def __init__(self, target_bucket, target_prefix, canonical_user, permission, display_name = None, email_addr = None, uri = None):
        self.req_dict = {
            # Set WRITE and READ_ACP permission for LDG to target bucket
	    'set_ldg_acl': '<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n  <Owner>\n    <ID>bl_test</ID>\n    <DisplayName>bl_test</DisplayName>\n  </Owner>\n  <AccessControlList>\n    <Grant>\n      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">\n        <ID>bl_test</ID>\n        <DisplayName>bl_test</DisplayName>\n      </Grantee>\n      <Permission>FULL_CONTROL</Permission>\n    </Grant>\n    <Grant>\n      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">\n        <URI>http://acs.amazonaws.com/groups/s3/LogDelivery</URI>\n      </Grantee>\n      <Permission>WRITE</Permission>\n    </Grant>\n    <Grant>\n      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">\n        <URI>http://acs.amazonaws.com/groups/s3/LogDelivery</URI>\n      </Grantee>\n      <Permission>READ_ACP</Permission>\n    </Grant>\n  </AccessControlList>\n</AccessControlPolicy>',
 
            # Enable Bucket Logging with LoggingEnabled
            # without others
            'without_others': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n  </LoggingEnabled>\n</BucketLoggingStatus>',
            # with TargetBucket
            'with_targetbucket': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket),
            # with TargetPrefix
            'with_targetprefix': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_prefix),
            # with TargetGrants
            'with_targetgrants': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetGrants></TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>',
            # with TargetGrants, Grant, Grantee, ID and Permission
            'with_targetgrants_grant_grantee_id_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">\n          <ID>%s</ID>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (canonical_user, permission),
            # with TargetBucket and TargetPrefix
            'with_targetbucket_and_targetprefix': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix),
            # with TargetBucket and TargetPrefix, but it's both null str
            'with_targetbucket_and_targetprefix_both_nullstr': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket></TargetBucket>\n    <TargetPrefix></TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>',
            # with TargetBucket and TargetPrefix, but TargetPrefix is null str
            'with_targetbucket_and_targetprefix_but_targetprefix_nullstr': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix></TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket),
            # with TargetBucket, TargetGrants, Grant, Grantee, ID and Permission
            'with_targetbucket_targetgrants_grant_grantee_id_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">\n          <ID>%s</ID>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, canonical_user, permission), 
            # with TargetPrefix, TargetGrants, Grant, Grantee, ID and Permission
            'with_targetprefix_targetgrants_grant_grantee_id_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">\n          <ID>%s</ID>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_prefix, canonical_user, permission),
            # with TargetBucket, TargetPrefix and TargetGrants
            'with_targetbucket_targetprefix_targetgrants': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants></TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix),
            # with TargetBucket, TargetPrefix, TargetGrants and Grant
            'with_targetbucket_targetprefix_targetgrants_Grant': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant></Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix),
            # with TargetBucket, TargetPrefix, TargetGrants, Grant and Grantee
            'with_targetbucket_targetprefix_targetgrants_grant_grantee': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">\n        </Grantee>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix),
            # with TargetBucket, TargetPrefix, TargetGrants, Grant and Permission
            'with_targetbucket_targetprefix_targetgrants_grant_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix, permission),
            # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee and Permission
            'with_targetbucket_targetprefix_targetgrants_grant_grantee_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix, permission),
            # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, email and Permission
            'with_targetbucket_targetprefix_targetgrants_grant_grantee_email_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="AmazonCustomerByEmail">\n          <EmailAddress>%s</EmailAddress>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix, email_addr, permission),
            # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, ID and Permission
            'with_targetbucket_targetprefix_targetgrants_grant_grantee_id_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">\n          <ID>%s</ID>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix, canonical_user, permission),
            #with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, URI and Permission
            'with_targetbucket_targetprefix_targetgrants_grant_grantee_uri_permission': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n    <TargetGrants>\n      <Grant>\n        <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">\n          <URI>%s</URI>\n        </Grantee>\n        <Permission>%s</Permission>\n      </Grant>\n    </TargetGrants>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (target_bucket, target_prefix, uri, permission),

            # Disable Bucket Logging
            'disable_bl': '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n</BucketLoggingStatus>'
}

def SetLDGACL(dest_bucket, req_xml):
    req_url = 'http://127.0.0.1:8000/' + dest_bucket + '?acl'
    res = requests.put(req_url, headers = req_headers, data = req_xml, auth = s3_user_authv2)
    if res.status_code != 200:
	print res.status_code
	print res.content
        print "SetLDGACL Failed!"


class Tester(object):
    def __init__(self):
        self.bucket_no = 0

    def get_req_url(self, source_bucket):
        return 'http://127.0.0.1:8000/' + source_bucket + '?logging'

    def put_req(self, url, req_data):
        return requests.put(url, headers = req_headers, data = req_data, auth = s3_user_authv2)

    def get_new_bucket(self):
        bucket_name = 'test-' + str(self.bucket_no)
        self.bucket_no += 1
        exec_command("s3cmd -c " + s3_cfg + " mb s3://" + bucket_name)
        return bucket_name

    def get_res_content(self, bucket):
        res_fhandle = exec_command_with_return("s3cmd -c " + s3_cfg + " accesslog s3://" + bucket)
        return res_fhandle.read()

    def verify(self, res_content, expect_res_content_list):
        verify_result = True
        for ele in expect_res_content_list:
            if (ele in res_content) == False:
                verify_result = False
                break
        return verify_result



class FuncTester(Tester):
    def __init__(self, req_xml_dict, target_bucket, target_prefix):
        Tester.__init__(self)
        self.m_req_xml_dict = req_xml_dict
        self.target_bucket = target_bucket
        self.target_prefix = target_prefix
   
    def prepare(self):
        exec_command("s3cmd -c " + s3_cfg + " mb s3://" + self.target_bucket)

    def run(self):
        self.test_enable_bl_without_other_params()
        self.test_enable_bl_with_targetbucket()
        self.test_enable_bl_with_targetprefix()
        self.test_enable_bl_with_targetgrants()
        self.test_enable_bl_with_targetgrants_grant_grantee_id_permission()
        self.test_enable_bl_with_targetbucket_and_targetprefix()
        self.test_enable_bl_with_targetbucket_and_targetprefix_but_both_nullstr()
        self.test_enable_bl_with_targetbucket_and_targetprefix_but_targetprefix_nullstr()
        self.test_enable_bl_with_targetbucket_targetgrants_grant_grantee_id_permission()
        self.test_enable_bl_with_targetprefix_targetgrants_grant_grantee_id_permission()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_permission()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee_permission()
        #self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_email_permission()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_id_permission()
        self.test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_uri_permission()
        self.test_disable_bl()
   
    def end(self): 
        exec_command("s3cmd -c " + s3_cfg + " rb s3://" + self.target_bucket)
        print 'Remove bucket %s' % (self.target_bucket)
        for i in range(self.bucket_no):
            exec_command("s3cmd -c " + s3_cfg + " accesslog s3://test-" + str(i) + " --no-access-logging")
            exec_command("s3cmd -c " + s3_cfg + " rb s3://test-" + str(i))
            print 'Remove bucket test-%d' % (i)

        
    def test_enable_bl_without_other_params(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['without_others']
        res = self.put_req(req_url, self.m_req_xml_dict['without_others'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_without_other_params                                                 %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_without_other_params                                                 %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_without_other_params                                                 %s' % (fail_display("FAIL"))

    def test_enable_bl_with_targetbucket(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket                                                    %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket                                                    %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket                                                    %s' % (fail_display("FAIL"))


    def test_enable_bl_with_targetprefix(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetprefix']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetprefix'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetprefix                                                    %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetprefix                                                    %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetprefix                                                    %s' % (fail_display("FAIL"))


    def test_enable_bl_with_targetgrants(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetgrants']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetgrants'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetgrants                                                    %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetgrants                                                    %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetgrants                                                    %s' % (fail_display("FAIL"))

    # with TargetGrants, Grant, Grantee, ID and Permission
    def test_enable_bl_with_targetgrants_grant_grantee_id_permission(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetgrants_grant_grantee_id_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetgrants_grant_grantee_id_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetgrants_grant_grantee_id_permission                        %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetgrants_grant_grantee_id_permission                        %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetgrants_grant_grantee_id_permission                        %s' % (fail_display("FAIL"))
    

    def test_enable_bl_with_targetbucket_and_targetprefix(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket + '/' + self.target_prefix]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_and_targetprefix'])
        if res.status_code == expect_dict['status_code'] and res.content == expect_dict['http_msg']:
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_and_targetprefix                                   %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_and_targetprefix                                   %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_and_targetprefix                                   %s' % (fail_display("FAIL"))

    # with TargetBucket and TargetPrefix, but it's both null str
    def test_enable_bl_with_targetbucket_and_targetprefix_but_both_nullstr(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'InvalidTargetBucketForLogging',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_and_targetprefix_both_nullstr']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_and_targetprefix_both_nullstr'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_and_targetprefix_but_both_nullstr                  %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_and_targetprefix_but_both_nullstr                  %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_and_targetprefix_but_both_nullstr                  %s' % (fail_display("FAIL"))

    # with TargetBucket and TargetPrefix, but TargetPrefix is null str
    def test_enable_bl_with_targetbucket_and_targetprefix_but_targetprefix_nullstr(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_and_targetprefix_but_targetprefix_nullstr'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_and_targetprefix_but_targetprefix_nullstr          %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_and_targetprefix_but_targetprefix_nullstr          %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_and_targetprefix_but_targetprefix_nullstr          %s' % (fail_display("FAIL"))
  
    # with TargetBucket, TargetGrants, Grant, Grantee, ID and Permission
    def test_enable_bl_with_targetbucket_targetgrants_grant_grantee_id_permission(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetgrants_grant_grantee_id_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetgrants_grant_grantee_id_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetgrants_grant_grantee_id_permission           %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetgrants_grant_grantee_id_permission           %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetgrants_grant_grantee_id_permission           %s' % (fail_display("FAIL"))

    # with TargetPrefix, TargetGrants, Grant, Grantee, ID and Permission 
    def test_enable_bl_with_targetprefix_targetgrants_grant_grantee_id_permission(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetprefix_targetgrants_grant_grantee_id_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetprefix_targetgrants_grant_grantee_id_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetprefix_targetgrants_grant_grantee_id_permission           %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetprefix_targetgrants_grant_grantee_id_permission           %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetprefix_targetgrants_grant_grantee_id_permission           %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix and TargetGrants
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket + '/' + self.target_prefix]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants                          %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants                          %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants                          %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants and Grant
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_Grant']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_Grant'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant                    %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant                    %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant                    %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants, Grant and Grantee
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee            %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee            %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee            %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants, Grant and Permission
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_permission(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_permission         %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_permission         %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_permission         %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee and Permission
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee_permission(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'MalformedXML',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee_permission %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee_permission %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_grantee_permission %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, email and Permission
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_email_permission(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket + '/' + self.target_prefix]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_email_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_email_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_email_permission   %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_email_permission   %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_email_permission   %s' % (fail_display("FAIL"))

    # with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, ID and Permission
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_id_permission(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket + '/' + self.target_prefix]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_id_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_id_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_id_permission      %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_id_permission      %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_id_permission      %s' % (fail_display("FAIL"))

    #with TargetBucket, TargetPrefix, TargetGrants, Grant, Grantee, URI and Permission
    def test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_uri_permission(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + self.target_bucket + '/' + self.target_prefix]}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
#        print self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_uri_permission']
        res = self.put_req(req_url, self.m_req_xml_dict['with_targetbucket_targetprefix_targetgrants_grant_grantee_uri_permission'])
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_uri_permission     %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_uri_permission     %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_targetbucket_targetprefix_targetgrants_grant_uri_permission     %s' % (fail_display("FAIL"))


    def test_disable_bl(self):
        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: False']}
        test_bucket = 'test-0'
        req_url = self.get_req_url(test_bucket)
        res = self.put_req(req_url, self.m_req_xml_dict['disable_bl'])
        if res.status_code == expect_dict['status_code'] and res.content == expect_dict['http_msg']:
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_disable_bl                                                                     %s' % (ok_display("OK"))
            else:
                print 'test_disable_bl                                                                     %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_disable_bl                                                                %s' % (fail_display("FAIL"))


class UsageTester(Tester):
    def __init__(self, req_xml_dict, ceph_path):
        Tester.__init__(self)
        self.m_req_xml_dict = req_xml_dict
        self.ceph_path = ceph_path
        self.test_bucket_dict = {}
    
    def prepare(self):
        exec_command("s3cmd -c " + s3_cfg + " mb s3://bucket-test-1")
        SetLDGACL('bucket-test-1', self.m_req_xml_dict['set_ldg_acl'])
        exec_command("s3cmd -c " + s3_cfg + " mb s3://bucket-test-2")
        SetLDGACL('bucket-test-2', self.m_req_xml_dict['set_ldg_acl'])
        exec_command("s3cmd -c " + s3_cfg_2 + " mb s3://bucket-test-3")
        
        # bl process can only be exec once a day
        # prepare test data
        test_bucket_list1 = self.test_enable_bl_one_sourcebucket_to_one_diff_targetbucket_test_data_prepare()
        self.test_bucket_dict['test_enable_bl_one_sourcebucket_to_one_diff_targetbucket'] = test_bucket_list1
        test_bucket_list2 = self.test_enable_bl_one_sourcebucket_to_one_same_targetbucket_test_data_prepare()
        self.test_bucket_dict['test_enable_bl_one_sourcebucket_to_one_same_targetbucket'] = test_bucket_list2
        test_bucket_list3 = self.test_enable_bl_multi_sourcebucket_to_one_target_bucket_test_data_prepare()
        self.test_bucket_dict['test_enable_bl_multi_sourcebucket_to_one_target_bucket'] = test_bucket_list3


    def run(self):
        self.test_enable_bl_one_sourcebucket_to_one_diff_targetbucket(self.test_bucket_dict['test_enable_bl_one_sourcebucket_to_one_diff_targetbucket'])
        self.test_enable_bl_one_sourcebucket_to_one_same_targetbucket(self.test_bucket_dict['test_enable_bl_one_sourcebucket_to_one_same_targetbucket'])
        self.test_enable_bl_disable_bl_and_enable_bl_again()
        self.test_enable_bl_multi_sourcebucket_to_one_target_bucket(self.test_bucket_dict['test_enable_bl_multi_sourcebucket_to_one_target_bucket'])
        self.test_enable_bl_with_other_user_targetbucket()

    def end(self):
        exec_command("s3cmd -c " + s3_cfg + " rb s3://bucket-test-1 --recursive")
        print 'Remove bucket bucket-test-1'
        exec_command("s3cmd -c " + s3_cfg + " rb s3://bucket-test-2 --recursive")
        print 'Remove bucket bucket-test-2'
        exec_command("s3cmd -c " + s3_cfg_2 + " rb s3://bucket-test-3 --recursive")
        print 'Remove bucket bucket-test-3'
        for i in range(self.bucket_no):
            exec_command("s3cmd -c " + s3_cfg + " accesslog s3://test-" + str(i) + " --no-access-logging")
            exec_command("s3cmd -c " + s3_cfg + " rb s3://test-" + str(i) + " --recursive")
            print 'Remove bucket test-%d' % (i)

    
    def bucket_opt(self, source_bucket):
        exec_command("s3cmd -c " + s3_cfg + " ls")
        exec_command("s3cmd -c " + s3_cfg + " put " + s3_cfg + " s3://" + source_bucket)

    def verify_op_result(self, source_bucket, target_bucket, target_prefix):
        fhandle = exec_command_with_return("s3cmd -c " + s3_cfg + " accesslog s3://" + source_bucket)
        op_result = fhandle.read()
        expect_result = "Access logging for: s3://%s/\n   Logging Enabled: True\n     Target prefix: s3://%s/%s\n" % (source_bucket, target_bucket, target_prefix)
        if op_result == expect_result:
            return True
        else:
            return False

    def test_enable_bl_one_sourcebucket_to_one_diff_targetbucket_test_data_prepare(self):
        bucket_list = []
        test_bucket = self.get_new_bucket()
        bucket_list.append(test_bucket)
        req_url = self.get_req_url(test_bucket)
        req_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>bucket-test-1</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket + '/')
        res = self.put_req(req_url, req_xml)
        if res.status_code == 200:
            return bucket_list
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_one_sourcebucket_to_one_diff_targetbucket_test_data_prepare          %s' % (fail_display("FAIL"))
            return []

    def test_enable_bl_one_sourcebucket_to_one_diff_targetbucket(self, test_bucket_list):
        result = True
        for test_bucket in test_bucket_list:
            if self.verify_op_result(test_bucket, 'bucket-test-1', test_bucket + '/') == False:
                result = False
                break
        if result == True:
            print 'test_enable_bl_one_sourcebucket_to_one_diff_targetbucket                            %s' % (ok_display("OK"))
        else:
            print 'test_enable_bl_one_sourcebucket_to_one_diff_targetbucket                            %s' % (fail_display("FAIL"))
             
    def test_enable_bl_one_sourcebucket_to_one_same_targetbucket_test_data_prepare(self):
        bucket_list = []
        test_bucket = self.get_new_bucket()
        SetLDGACL(test_bucket, self.m_req_xml_dict['set_ldg_acl'])
        bucket_list.append(test_bucket)
        req_url = self.get_req_url(test_bucket)
        req_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket, test_bucket + '/')
        res = self.put_req(req_url, req_xml)
        if res.status_code == 200:
            return bucket_list
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_one_sourcebucket_to_one_same_targetbucket_test_data_prepare          %s' % (fail_display("FAIL"))
            return []

    def test_enable_bl_one_sourcebucket_to_one_same_targetbucket(self, test_bucket_list):
        result = True
        for test_bucket in test_bucket_list:
            if self.verify_op_result(test_bucket, test_bucket, test_bucket + '/') == False:
                result = False
                break
        if result == True:
            print 'test_enable_bl_one_sourcebucket_to_one_same_targetbucket                            %s' % (ok_display("OK"))
        else:
            print 'test_enable_bl_one_sourcebucket_to_one_same_targetbucket                            %s' % (fail_display("FAIL"))
        

    def test_enable_bl_disable_bl_and_enable_bl_again(self):
        test_bucket = self.get_new_bucket()
        SetLDGACL(test_bucket, self.m_req_xml_dict['set_ldg_acl'])
        req_url = self.get_req_url(test_bucket)
        enable_req_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>%s</TargetBucket>\n    <TargetPrefix>log/</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket)
        disable_req_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n</BucketLoggingStatus>'
        res = self.put_req(req_url, enable_req_xml)
        res = self.put_req(req_url, disable_req_xml)
        res = self.put_req(req_url, enable_req_xml)

        expect_dict = {"status_code": 200,
                       "http_msg": '',
                       "content": ['Logging Enabled: True', 'Target prefix: s3://' + test_bucket + '/log/']}
        if res.status_code == expect_dict['status_code'] and res.content == expect_dict['http_msg']:
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_disable_bl_and_enable_bl_again                                       %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_disable_bl_and_enable_bl_again                                       %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_disable_bl_and_enable_bl_again                                       %s' % (fail_display("FAIL"))

    def test_enable_bl_multi_sourcebucket_to_one_target_bucket_test_data_prepare(self):
        bucket_list = []
        test_bucket1 = self.get_new_bucket()
        bucket_list.append(test_bucket1)
        test_bucket2 = self.get_new_bucket()
        bucket_list.append(test_bucket2)
        test_bucket3 = self.get_new_bucket()
        bucket_list.append(test_bucket3)

        req_url1 = self.get_req_url(test_bucket1)
        req_url2 = self.get_req_url(test_bucket2)
        req_url3 = self.get_req_url(test_bucket3)
        req_xml1 = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>bucket-test-2</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket1 + '/')
        req_xml2 = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>bucket-test-2</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket2 + '/')
        req_xml3 = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>bucket-test-2</TargetBucket>\n    <TargetPrefix>%s</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>' % (test_bucket3 + '/')

        res1 = self.put_req(req_url1, req_xml1)
        res2 = self.put_req(req_url2, req_xml2)
        res3 = self.put_req(req_url3, req_xml3)

        if res1.status_code == res2.status_code == res3.status_code == 200:
            return bucket_list
        else:
            print res1.status_code, res1.content
            print res2.status_code, res2.content
            print res3.status_code, res3.content
            print 'test_enable_bl_one_sourcebucket_to_one_diff_targetbucket_test_data_prepare          %s' % (fail_display("FAIL"))
            return []


    def test_enable_bl_multi_sourcebucket_to_one_target_bucket(self, test_bucket_list):
        result = True
        for test_bucket in test_bucket_list:
            if self.verify_op_result(test_bucket, 'bucket-test-2', test_bucket + '/') ==  False:
                result = False
                break
        if result == True:
            print 'test_enable_bl_multi_sourcebucket_to_one_target_bucket                              %s' % (ok_display("OK"))
        else:
            print 'test_enable_bl_multi_sourcebucket_to_one_target_bucket                              %s' % (fail_display("FAIL"))
        

    def test_enable_bl_with_other_user_targetbucket(self):
        expect_dict = {"status_code": 400,
                       "http_msg": 'InvalidTargetBucketForLogging',
                       "content": ['Logging Enabled: False']}
        test_bucket = self.get_new_bucket()
        req_url = self.get_req_url(test_bucket)
        req_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">\n  <LoggingEnabled>\n    <TargetBucket>bucket-test-3</TargetBucket>\n    <TargetPrefix>log/</TargetPrefix>\n  </LoggingEnabled>\n</BucketLoggingStatus>'
#        print req_xml
        res = self.put_req(req_url, req_xml)
        if (res.status_code == expect_dict['status_code']) and (expect_dict['http_msg'] in res.content):
            content = self.get_res_content(test_bucket)
            if self.verify(content, expect_dict['content']):
                print 'test_enable_bl_with_other_user_targetbucket                                         %s' % (ok_display("OK"))
            else:
                print 'test_enable_bl_with_other_user_targetbucket                                         %s' % (fail_display("FAIL"))
        else:
            print res.status_code
            print res.content
            print 'test_enable_bl_with_other_user_targetbucket                                         %s' % (fail_display("FAIL"))


def test_rgw_create_bl_deliver_by_systemuser_http():
    expect_dict = {'status_code': 200,
                   'http_msg': ['"user_id":"bl_deliver_create"', '"user":"bl_deliver_create"', '"access_key":"bl_deliver_create"', '"secret_key":"bl_deliver_create"']
            }
    req_url = 'http://127.0.0.1:8000/admin/user?format=json&uid={uid}&access-key={access_key}&secret-key={secret_key}&display-name={display_name}&bl_deliver=true'.format(uid='bl_deliver_create', access_key='bl_deliver_create', secret_key='bl_deliver_create', display_name='bl_deliver_create')
    res = requests.put(req_url, auth=S3Auth('system_user', 'system_user', '127.0.0.1:8000'))

    result = True
    if res.status_code == expect_dict['status_code']:
        for ele in expect_dict['http_msg']:
            if (ele in res.content) != True:
                result = False
                break
    else:
        result = False

    if result:
        print 'test_rgw_create_bl_deliver_by_systemuser_http                                       %s' % (ok_display("OK"))
    else:
        print res.status_code, res.content
        print 'test_rgw_create_bl_deliver_by_systemuser_http                                       %s' % (fail_display("FAIL"))


def test_rgw_create_bl_deliver_by_commonuser_http():
    expect_dict = {'status_code': 403,
                   'http_msg': ['"Code":"AccessDenied"']
            }
    req_url = 'http://127.0.0.1:8000/admin/user?format=json&uid={uid}&access-key={access_key}&secret-key={secret_key}&display-name={display_name}&bl_deliver=true'.format(uid='bl_deliver_create2', access_key='bl_deliver_create2', secret_key='bl_deliver_create2', display_name='bl_deliver_create2')
    res = requests.put(req_url, auth=S3Auth('bl_test', 'bl_test', '127.0.0.1:8000'))

    result = True
    if res.status_code == expect_dict['status_code']:
        for ele in expect_dict['http_msg']:
            if (ele in res.content) != True:
                result = False
                break
    else:
        result = False

    if result:
        print 'test_rgw_create_bl_deliver_by_commonuser_http                                       %s' % (ok_display("OK"))
    else:
        print res.status_code, res.content
        print 'test_rgw_create_bl_deliver_by_commonuser_http                                       %s' % (fail_display("FAIL"))




# Parsing Command Line Params
def ParseCommandLine():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-bucket-name', action = 'store', dest = 'source_bucket_name', default = '')
    parser.add_argument('--uid', action = 'store', dest = 'canonical_id', default = '')
    # Can input display name or not
    parser.add_argument('--display-name', action = 'store', dest = 'display_name', default = '')
    parser.add_argument('--target-bucket', action = 'store', dest = 'target_bucket', default = '')
    parser.add_argument('--target-prefix', action = 'store', dest = 'target_prefix', default = '')
    parser.add_argument('--ceph-path', action = 'store', dest = 'ceph_path', default = '')
    parser.add_argument('--opt-type', action = 'store', dest = 'opt_type', default = '')
    result = parser.parse_args()
    return result

# Get Canonical ID and Display Name
def GetCanonicalIDandDisplayName(source_bucket):
    req_url = 'http://127.0.0.1:8000/' + source_bucket + '?acl'
    res = requests.get(req_url, headers = req_headers, auth = s3_user_authv2)
    print res.status_code
    print res.content

if __name__ == '__main__':
    cmd_line_param = ParseCommandLine()
    source_bucket = cmd_line_param.source_bucket_name
    canonical_id = cmd_line_param.canonical_id
    display_name = cmd_line_param.display_name
    target_bucket = cmd_line_param.target_bucket
    target_prefix = cmd_line_param.target_prefix
    ceph_path = cmd_line_param.ceph_path
    opt_type = cmd_line_param.opt_type

    all_req_xml = ReqXml(target_bucket, target_prefix, canonical_id, 'READ', display_name, '', 'http://acs.amazonaws.com/groups/s3/LogDelivery')

    if opt_type == '':
        print 'Opt type is necessary!'
    else:
        # Get Canonical ID and Display Name Before Run test
        if opt_type == 'get_id':
            if source_bucket == '':
                print 'When you get canonical id, source bucket name is necessary!'
            else:
                GetCanonicalIDandDisplayName(source_bucket)
        # Set LDG WRITE and READ_ACP permission to target bucket
        elif opt_type == 'set_acl':
	    if target_bucket == '':
	        print 'When you set LDG ACL, target bucket name is necessary!'
	    else:
		SetLDGACL(target_bucket, all_req_xml.req_dict['set_ldg_acl'])
        # Function Test
        elif opt_type == 'run_func_test':
            if target_bucket == '':
                print 'When you test BL, target bucket name is necessary!'
            else:
                func_tester = FuncTester(all_req_xml.req_dict, target_bucket, target_prefix)
                func_tester.prepare()
                func_tester.run()
                func_tester.end()
        # Usage Scenario Test
        elif opt_type == 'run_usage_test':
            usage_tester = UsageTester(all_req_xml.req_dict, ceph_path)
            usage_tester.prepare()
            usage_tester.run()
#            usage_tester.end()
        elif opt_type == 'run_rgw_test':
            test_rgw_create_bl_deliver_by_systemuser_http()
            test_rgw_create_bl_deliver_by_commonuser_http()


