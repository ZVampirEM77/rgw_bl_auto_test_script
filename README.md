# rgw\_bl\_auto\_test\_script

当前RGW存储桶日志自动化测试脚本主要分为三部分的测试：

+  功能模块测试          opt-type = rgw\_func\_test

+  使用场景测试          opt-type = run\_usage\_test

+  RGW内部条件限制测试   opt-type = run\_rgw\_test

除此之外，还包括功能：

+  获取账户canonical id  opt-type = get\_id

+  设置target bucket acl opt-type = set\_acl

## 测试准备工作
Ceph集群启动后，确保ops\_log相关配置项已经开启，且bl的配置项也已配置：

rgw bl url = "http://localhost:8000"

rgw enable ops log = true

然后需要创建如下用户:

+ 系统用户

> ./radosgw-admin user create --uid=system\_user --access-key=system\_user --secret-key=system\_user --display-name="system\_user" --system

+ 测试所需用户

> ./radosgw-admin user create --uid=bl\_test --access-key=bl\_test --secret-key=bl\_test --display-name="bl\_test"

> ./radosgw-admin user create --uid=bl\_test2 --access-key=bl\_test2 --secret-key=bl\_test2 --display-name="bl\_test2"

然后需要创建测试所需的target bucket：

> cd rgw\_bl\_auto\_test\_script/

> s3cmd -c bl\_test.s3cfg mb s3://tbucket


## 测试操作
### 功能模块测试
对于功能模块测试来说，所必须的输入参数包括:

+ uid(即canonical id, 可以通过opt\_type = get\_id 功能来获取)

+ ceph-path(即vstart.sh所在目录位置)

+ target-bucket(即上面所创建的target bucket)

+ opt-type = run\_func\_test

eg:

> python BucketLoggingAutoTest.py --ceph-path=../ceph/src/ --target-bucket=tbucket --uid=bl\_test --opt-type=run\_func\_test


### 使用场景测试
对于使用场景测试来说，所必须的输入参数包括:

+ ceph-path

+ opt-type = run\_usage\_test

eg:

> python BucketLoggingAutoTest.py --ceph-path=../ceph/src/ --opt-type=run\_usage\_test


### RGW内部条件限制测试
对于RGW相关的测试，目前主要是针对\* 只有system user可以通过HTTP请求创建bl\_deliver \* 这一限制进行测试，所必须的输入参数包括:

+ ceph-path

+ opt-type = run\_rgw\_test

eg:

> python BucketLoggingAutoTest.py --ceph-path=../ceph/src/ --opt-type=run\_rgw\_test


## 其他功能
### 获取账户canonical id
主要是针对source-bucket获取其owner的canonical id, 所必须的参数包括:

+ ceph-path

+ source-bucket

+ opt-type = get\_id

eg:

> python BucketLoggingAutoTest.py --ceph-path=../ceph/src/ --source-bucket=sbucket --opt-type=get\_id


### 设置target bucket acl
主要是用于设置LDG对于target bucket的操作权限，所必须的参数包括:

+ ceph-path

+ target-bucket

+ opt-type = set\_acl
