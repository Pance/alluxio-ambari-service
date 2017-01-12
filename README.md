## Alluxio Service for Ambari 2.2 (IOP 4.X tech preview)

Alluxio v 1.0.1 - Deploys on IOP 4.X tech preview


Install, start/stop, status, service check functional


**1. Clone the service into the dir for the Stack you are running in Ambari**

**- Adding Alluxio to a BigInsights 4.x tech preview Cluster**

```
# Clone the service deployer
git clone https://github.com/chuyqa/alluxio-ambari-service /var/lib/ambari-server/resources/stacks/BigInsights/4.3/services/ALLUXIO

#git has a 100mb file limit, download alluxio source to your stack dir
wget http://alluxio.org/downloads/files/1.0.1/alluxio-1.0.1-bin.tar.gz -P /var/lib/ambari-server/resources/stacks/BigInsights/4.3/services/ALLUXIO/package/files 

ambari-server restart

```


**2. Add service via Ambari ui**



**3. Assign a Alluxio Master And Worker nodes.**

By default the master will also run a worker 


Once Service is started, you may access Alluxio Master Web UI on ***alluxio.master.hostname*:19999**

**Future Work:**
Use non-root user 
defaultFS url
Metrics
Fix status check on start
Clean up & Expand alluxio-env
