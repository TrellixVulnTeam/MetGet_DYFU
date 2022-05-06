#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 ADCIRC Development Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from metbuild.cloudwatch import CloudWatch
logger = CloudWatch()

# Function to genreate a date range
def datespan(startDate, endDate, delta):
    from datetime import datetime,timedelta
    currentDate = startDate
    while currentDate <= endDate:
        yield currentDate
        currentDate += delta

def generate_datatype_key(data_type):
    import pymetbuild
    if data_type == "wind_pressure":
        return pymetbuild.Meteorology.WIND_PRESSURE
    elif data_type == "pressure":
        return pymetbuild.Meteorology.PRESSURE
    elif data_type == "wind":
        return pymetbuild.Meteorology.WIND
    elif data_type == "rain":
        return pymetbuild.Meteorology.RAINFALL
    elif data_type == "humidity":
        return pymetbuild.Meteorology.HUMIDITY
    elif data_type == "temperature":
        return pymetbuild.Meteorology.TEMPERATURE
    elif data_type == "ice":
        return pymetbuild.Meteorology.ICE
    else:
        raise RuntimeError("Invalid data type requested")


def generate_met_field(output_format, start, end, time_step, filename, compression):
    import pymetbuild
    if output_format == "ascii" or output_format == "owi-ascii" or output_format == "adcirc-ascii":
        return pymetbuild.OwiAscii(start,end,time_step,compression)
    elif output_format == "owi-netcdf" or output_format == "adcirc-netcdf":
        return pymetbuild.OwiNetcdf(start,end,time_step, filename)
    elif output_format == "hec-netcdf":
        return pymetbuild.RasNetcdf(start,end,time_step, filename)
    elif output_format == "delft3d":
        return pymetbuild.DelftOutput(start,end,time_step,filename)
    elif output_format == "raw":
        return None
    else:
        raise RuntimeError("Invalid output format selected: "+output_format)


def generate_met_domain(inputData, met_object, index):
    import pymetbuild
    d = inputData.domain(index)
    output_format = inputData.format()
    if output_format == "ascii" or output_format == "owi-ascii" or output_format == "adcirc-ascii":
        if inputData.data_type() == "wind_pressure":
            fn1 = inputData.filename()+"_"+"{:02d}".format(index)+".pre"
            fn2 = inputData.filename()+"_"+"{:02d}".format(index)+".wnd"
            fns = [fn1, fn2]
        elif inputData.data_type() == "rain":
            fns = [ inputData.filename()+".precip" ]
        elif inputData.data_type() == "humidity":
            fns = [ inputData.filename()+".humid" ]
        elif inputData.data_type() == "ice":
            fns = [ inputData.filename()+".ice" ]
        else:
            raise RuntimeError("Invalid variable requested")
        if inputData.compression():
            for i,s in enumerate(fns):
                fns[i] = s+".gz"
                
        met_object.addDomain(d.grid().grid_object(), fns)
    elif output_format == "owi-netcdf":
        group = d.service() 
        met_object.addDomain(d.grid().grid_object(), [group])
    elif output_format == "hec-netcdf":
        if inputData.data_type() == "wind_pressure":
            variables = [ "wind_u", "wind_v", "mslp" ]
        elif inputData.data_type() == "wind":
            variables = [ "wind_u", "wind_v" ]
        elif inputData.data_type() == "rain":
            variables = [ "rain" ]
        elif inputData.data_type() == "humidity":
            variables = [ "humidity" ]
        elif inputData.data_type() == "ice":
            variables = [ "ice" ]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    elif output_format == "delft3d":
        if inputData.data_type() == "wind_pressure":
            variables = [ "wind_u", "wind_v", "mslp" ]
        elif inputData.data_type() == "wind":
            variables = [ "wind_u", "wind_v" ]
        elif inputData.data_type() == "rain":
            variables = [ "rain" ]
        elif inputData.data_type() == "humidity":
            variables = [ "humidity" ]
        elif inputData.data_type() == "ice":
            variables = [ "ice" ]
        else:
            raise RuntimeError("Invalid variable requested")
        met_object.addDomain(d.grid().grid_object(), variables)
    else:
        raise RuntimeError("Invalid output format selected: "+output_format)

def merge_atcf_advisories(best_track_file, advisory_file, output_file):

    merged_atcf = []

    with open(best_track_file,'r') as btk, open(advisory_file,'r') as adv:

        #...Read and clean up the atcf files
        btk_data = btk.read().split("\n")
        adv_data = adv.read().split("\n")
        for d in btk_data:
            d = d.strip()

        for d in adv_data:
            d = d.strip()

        if btk_data[-1] == "":
            btk_data = btk_data[0:-1]

        if adv_data[-1] == "":
            adv_data = adv_data[0:-1]

        #...Compute the dates before merging
        btk_dates = compute_atcf_datetimes(btk_data)
        adv_dates = compute_atcf_datetimes(adv_data)

        #...Write the best track up until the advisory starts
        i = 0
        for d in btk_dates:
            if d >= adv_dates[0]:
                break
            else:
                merged_atcf.append(btk_data[i])
            i += 1

        for line in adv_data:
            merged_atcf.append(line)

    if output_file:
        with open(output_file,'w') as out:
            for line in merged_atcf:
                out.write(line+"\n")

    return merged_atcf

        

def compute_atcf_datetimes(atcf_data) -> list:
    from datetime import datetime, timedelta
    dates = []
    for line in atcf_data:
        cols = line.split(",")
        base_time = datetime.strptime(cols[2]," %Y%m%d%H")
        forecast_time = base_time + timedelta(hours=int(cols[5]))
        dates.append(forecast_time)
    return dates


# Main function to process the message and create the output files and post to S3
def process_message(json_message, queue, json_file=None) -> bool:
    import time
    import json
    import pymetbuild
    import datetime
    import os
    import json
    import sys
    from metbuild.instance import Instance
    from metbuild.input import Input
    from metbuild.database import Database
    from metbuild.s3file import S3file

    filelist_name = "filelist.json"

    instance = Instance()

    instance.enable_termination_protection()
    
    db = Database()

    if json_file:
        logger.info("Processing message from file: "+json_file)
        with open(json_file) as f:
            json_data = json.load(f)
        inputData = Input(json_data,None,None,None)
    else:
        logger.info("Processing message with id: "+json_message["MessageId"])
        messageId = json_message["MessageId"]
        logger.info(json_message['Body'])
        inputData = Input(json.loads(json_message['Body']), logger, queue, json_message["ReceiptHandle"])
        
    start_date = inputData.start_date()
    start_date_pmb = inputData.start_date_pmb()
    end_date = inputData.end_date()
    end_date_pmb = inputData.end_date_pmb()
    time_step = inputData.time_step()

    s3 = S3file(os.environ["OUTPUT_BUCKET"])

    if not inputData.format() == "raw":
        met_field = generate_met_field(inputData.format(), start_date_pmb, end_date_pmb, time_step, inputData.filename(), inputData.compression())

    nowcast = inputData.nowcast()
    multiple_forecasts = inputData.multiple_forecasts()
    data_type_key = generate_datatype_key(inputData.data_type())

    domain_data = []
    ongoing_restore = False
    db_files = []
    #...Take a first pass on the data and check for restore status
    for i in range(inputData.num_domains()):
      if not inputData.format() == "raw":
        generate_met_domain(inputData, met_field, i) 
      d = inputData.domain(i)
      f = db.generate_file_list(d.service(),inputData.data_type(),start_date,end_date,d.storm(),nowcast,multiple_forecasts,d.year(),d.basin(),d.advisory()) 
      db_files.append(f)
      if len(f) < 2:
        logger.error("No data found for domain "+str(i)+". Giving up.")
        if not json_file:
          logger.debug("Deleting message "+message["MessageId"]+" from the queue")
          queue.delete_message(message["ReceiptHandle"])
        sys.exit(1)

      if d.service() == "nhc":
        ongoing_restore_btk = db.check_initiate_restore(f["best_track"],d.service())
        ongoing_restore_adv = db.check_initiate_restore(f["advisory"],d.service())

        if ongoing_restore_btk or ongoing_restore_adv:
            ongoing_restore = True

      else:    
        for item in f:
          ongoing_restore_this = db.check_initiate_restore(item[1],d.service())
          if ongoing_restore_this:
            ongoing_restore = True
    
    #...If restore ongoing, this is where we stop
    if ongoing_restore:
        if not json_file:
          db.update_request_status(json_message["MessageId"], "restore", "Job is in archive restore status", json_message["Body"],False)
        ff = met_field.filenames()
        for f in ff:
          os.remove(f)
        cleanup_temp_files(domain_data)
        return False
   
    #...Begin downloading data from s3
    for i in range(inputData.num_domains()):
      d = inputData.domain(i)
      f = db_files[i] 
      if not d.service() == "nhc":
        if len(f) < 2:
          logger.error("No data found for domain "+str(i)+". Giving up.")
          if not json_file:
            logger.debug("Deleting message "+message["MessageId"]+" from the queue")
            queue.delete_message(message["ReceiptHandle"])
          sys.exit(1)

      if d.service() == "nhc":
        best_track_file = db.get_file(f["best_track"],d.service())
        advisory_file = db.get_file(f["advisory"],d.service())
        domain_data.append({"best_track": best_track_file, "advisory": advisory_file})
      else:
         domain_data.append([])
         for item in f:
          local_file = db.get_file(item[1],d.service(),item[0])
          domain_data[i].append({"time":item[0],"filepath":local_file})
          
    #...Output data for filelist.json
    output_file_list=[]
    files_used_list={}

    #...If raw, then we move the files to the current directory
    if inputData.format() == "raw":
      for i in range(inputData.num_domains()):
        d = inputData.domain(i)
        if d.service() == "nhc":
          adv_file = os.path.basename(domain_data[i]["advisory"])
          btk_file = os.path.basename(domain_data[i]["best_track"])
          if btk_file and adv_file:
            output_file = "nhc_merged_year_{:04d}_storm_{:02d}_advisory_{:02d}.trk".format(inputData.domain(i).year(),inputData.domain(i).storm(),inputData.domain(i).advisory())
            merge_atcf_advisories(domain_data[i]["best_track"], domain_data[i]["advisory"], output_file)
          elif btk_file and not adv_file:
            output_file = btk_file
          elif adv_file and not btk_file:
            output_file = adv_file  
          files_used_list[d.name()] = []
          files_used_list[d.name()].append(btk_file)
          files_used_list[d.name()].append(adv_file)
          output_file_list.append(output_file)
        else:
          files_used_list[d.name()] = []
          for f in d:
            fn = os.path.basename(f["filepath"])
            os.rename(f["filepath"],fn)
            output_file_list.append(fn)
            files_used_list.append(fn)

    else:
      #...otherwise, we will interpolate to a grid
  
      def get_next_file_index(time, domain_data):
          for i in range(len(domain_data)):
              if time <= domain_data[i]["time"]:
                  return i
          return len(domain_data)-1
  
      for i in range(inputData.num_domains()):
          d = inputData.domain(i)
          met = pymetbuild.Meteorology(d.grid().grid_object(),data_type_key,inputData.backfill(),inputData.epsg())
  
          t0 = domain_data[i][0]["time"]
  
          domain_files_used = []
          next_time = start_date + datetime.timedelta(seconds=time_step)
          index = get_next_file_index(next_time, domain_data[i])
  
          t1 = domain_data[i][index]["time"]
          t0_pmb = Input.date_to_pmb(t0)
          t1_pmb = Input.date_to_pmb(t1)
          met.set_next_file(domain_data[i][0]["filepath"])
          domain_files_used.append(os.path.basename(domain_data[i][0]["filepath"]))
  
          met.set_next_file(domain_data[i][index]["filepath"])
          domain_files_used.append(os.path.basename(domain_data[i][index]["filepath"]))
  
          for t in datespan(start_date,end_date,datetime.timedelta(seconds=time_step)): 
              if t > t1:
                  index = get_next_file_index(t, domain_data[i])
                  t0 = t1
                  t1 = domain_data[i][index]["time"]
                  met.set_next_file(domain_data[i][index]["filepath"])
                  domain_files_used.append(os.path.basename(domain_data[i][index]["filepath"]))
                  met.process_data()
              #print(i,index,len(domain_data[i]),t,t0,t1,end="",flush=True)
              if t < t0 or t > t1:
                  weight = -1.0
              else:
                  weight = met.generate_time_weight(Input.date_to_pmb(t0),
                      Input.date_to_pmb(t1),Input.date_to_pmb(t))
              #print(" -->  ",weight,flush=True)
              if inputData.data_type() == "wind_pressure":
                  values = met.to_wind_grid(weight)
              else:
                  values = met.to_grid(weight)
              met_field.write(Input.date_to_pmb(t),i,values)
  
          files_used_list[inputData.domain(i).name()] =  domain_files_used
          
      output_file_list = met_field.filenames()
      met_field = None #...Closes all open files
  
    output_file_dict = {"input": inputData.json(), "input_files":files_used_list, "output_files":output_file_list}

    #...Posts the data out to the correct S3 location
    if not json_file:
        for f in output_file_list:
            path = messageId+"/"+f
            s3.upload_file(f,path)
            os.remove(f)

    with open(filelist_name,'w') as of:
        of.write(json.dumps(output_file_dict,indent=2))

    if json_file:
        logger.info("Finished processing file: "+json_file)
    else:
        filelist_path = messageId+"/"+filelist_name
        s3.upload_file(filelist_name,filelist_path)
        logger.info("Finished processing message with id: "+json_message["MessageId"])
        os.remove(filelist_name)

    cleanup_temp_files(domain_data)

    instance.disable_termination_protection()

    return True


def cleanup_temp_files(data):
    import os
    from os.path import exists
    for domain in data:
        if type(domain) == list:
            for f in domain:
                if exists(f["filepath"]):
                    os.remove(f["filepath"])
        elif type(domain) == dict:
            if exists(domain["best_track"]):
                os.remove(domain["best_track"])
            if exists(domain["advisory"]):
                os.remove(domain["advisory"])


def initialize_environment_variables():
    import os
    import boto3
    import requests

    region = requests.get("http://169.254.169.254/latest/meta-data/placement/availability-zone").text[0:-1]
    ec2 = boto3.client("ec2",region_name=region)
    ssm = boto3.client("ssm",region_name=region)
    stackname = ec2.describe_tags(Filters=[{"Name":"key","Values":["aws:cloudformation:stack-name"]}])["Tags"][0]["Value"]
    dbpassword = ssm.get_parameter(Name=stackname+"-dbpassword")["Parameter"]["Value"]
    dbusername = ssm.get_parameter(Name=stackname+"-dbusername")["Parameter"]["Value"]
    dbserver = ssm.get_parameter(Name=stackname+"-dbserver")["Parameter"]["Value"]
    dbname = ssm.get_parameter(Name=stackname+"-dbname")["Parameter"]["Value"]
    bucket = ssm.get_parameter(Name=stackname+"-bucket")["Parameter"]["Value"]
    outbucket = ssm.get_parameter(Name=stackname+"-outputbucket")["Parameter"]["Value"]
    queue = ssm.get_parameter(Name=stackname+"-queue")["Parameter"]["Value"]

    os.environ["DBPASS"] = dbpassword
    os.environ["DBUSER"] = dbusername
    os.environ["DBSERVER"] = dbserver
    os.environ["DBNAME"] = dbname
    os.environ["BUCKET"] = bucket
    os.environ["OUTPUT_BUCKET"] = outbucket
    os.environ["QUEUE_NAME"] = queue
    os.environ["AWS_DEFAULT_REGION"] = region


# Main function
# Check for a message in the queue. If it exists, process it
# otherwise, we're outta here
def main():
    from metbuild.queue import Queue
    from metbuild.database import Database
    import sys
    import os

    logger.debug("Beginning execution")

    initialize_environment_variables()

    if len(sys.argv)==2:
        jsonfile = sys.argv[1]
        if os.path.exists(jsonfile): 
            process_message(None,None,json_file=jsonfile)
        else:
            print("[ERROR]: File "+jsonfile+" does not exist.")
            exit(1)
    else:
        queue = Queue(logger)
        has_message,message = queue.get_next_message()
        if has_message:
            logger.debug("Found message in queue. Beginning to process")
            try: 
                db = Database()
                request_status = db.query_request_status(message["MessageId"])
                if request_status["try"] > 4:
                    db.update_request_status(message["MessageId"], "error", "Removed due to multiple failures", message["Body"],False)
                    queue.delete_message(message["ReceiptHandle"])  
                    logger.debug("Message "+message["MessageId"]+" has had multiple failures. It has been deleted from the queue")
                elif request_status["status"] == "error":
                    queue.delete_message(message["ReceiptHandle"])  
                    db.update_request_status(message["MessageId"], "error", "Job exited with error", message["Body"],False)
                    logger.debug("Message "+message["MessageId"]+" has had an error. It has been deleted from the queue")
                else:
                    db.update_request_status(message["MessageId"], "running", "Job has begun running", message["Body"],True)
                    remove_message = process_message(message, queue)
                    if remove_message:
                        db.update_request_status(message["MessageId"], "completed", "Job has completed successfully", message["Body"],False)
                        logger.debug("Deleting message "+message["MessageId"]+" from the queue")
                        queue.delete_message(message["ReceiptHandle"])
                    else:
                        db.update_request_status(message["MessageId"], "restore", "Job is in archive restore status", message["Body"],False,True)
                        queue.release_message(message["ReceiptHandle"])
            except Exception as e:
                logger.debug("Deleting message "+message["MessageId"]+" from the queue")
                logger.debug("ERROR: "+str(e))
                queue.delete_message(message["ReceiptHandle"])  
                db.update_request_status(message["MessageId"], "error", "Job exited with uncaught error", message["Body"],False)
                print(str(e))
        else:
            logger.info("No message available in queue. Shutting down.")

    logger.debug("Exiting script with status 0")
    exit(0)


if __name__ == "__main__":
    main()
