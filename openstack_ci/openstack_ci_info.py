import datetime
import logging
from multiprocessing import Process

import requests
import json
import time


def moulinette_json(json_file):
    """
        Gets only the info we need, build_uuid and timestamps and builds a dictionary from them,
        returning an array of build_uuid (str) who have taken over 15min to build (most likely to be openstack
        deployment
        :param json_file: the json file answer from logstash
        :return: a list of str
    """
    result_file = json_file["hits"]["hits"]
    result_dict = {}
    for source in result_file:
        source = source["_source"]
        if type(source["build_uuid"]) == list:
            for i in source["build_uuid"]:
                if i not in result_dict.keys():
                    result_dict[i] = [source["@timestamp"]]
                else:
                    result_dict[i].append(source["@timestamp"])
        elif source["build_uuid"] not in result_dict.keys():
            result_dict[source["build_uuid"]] = [source["@timestamp"]]
        else:
            result_dict[source["build_uuid"]].append(source["@timestamp"])
    built_openstacks = get_built_openstacks(result_dict)
    return built_openstacks


def get_built_openstacks(result_dict):
    """
        Checks that build_uuids have timestamps showing longer than 15min time -> deployment and
        returns the array of uuids
        :param result_dict:
        :return:
    """
    built_openstacks = []
    for build in result_dict:
        max_timestamp = ""
        min_timestamp = ""
        for timestamp in result_dict[build]:
            element_time = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            if min_timestamp == "":
                min_timestamp = element_time
            if max_timestamp == "":
                max_timestamp = element_time
            if element_time > max_timestamp:
                max_timestamp = element_time
            if element_time < min_timestamp:
                min_timestamp = element_time
        total_time = max_timestamp - min_timestamp
        if total_time.seconds / 60 > 15:
            built_openstacks.append(build)
    return built_openstacks


def get_log_index_uris():
    """
        Get the uri beginnings for the recent logs for logstash
        We take the days between current date - 1 (current date logs might be incomplete)
        and current date - 6
        :return: an array of str
    """
    logstash_index_base = "http://logstash.openstack.org/elasticsearch/logstash-"
    logstash_indexes = []
    project = '"openstack/kolla-ansible"'
    for i in range(5):
        date_to_add = datetime.datetime.now() - datetime.timedelta(days=i+1)
        month = date_to_add.month
        day = date_to_add.day
        year = date_to_add.year
        print(date_to_add)
        print(month)
        print(day)
        print(year)
        uri = "{base}{year}.{month}.{day}/_search?q=project:{project}".format(
            base=logstash_index_base,
            year=year,
            month=f"{month:02d}",
            day=f"{day:02d}",
            project=project)
        logstash_indexes.append(uri)
    return logstash_indexes


def save_results(res, filename):
    """
        Saves the results in a file
    """
    filepath = "results/{fn}".format(fn=filename)
    with open(filepath, "w") as f:
        for i in res:
            f.write(i)
            f.write("\n")


def get_info_for_one_uri(uri, post_request):
    """
        Processes calls to get the logstash information about kolla-ansible log messages
        :param uri:
        :param post_request: the information necessary to get the proper sized information
            (dict with "from" and "size" values
        :return: nothing, it saves in a file results/result_[date]_[hits]
    """
    date = uri.replace('/_search?q=project:"openstack/kolla-ansible"', "")
    date = date.replace("http://logstash.openstack.org/elasticsearch/logstash-", "")

    print("Request for {uri}".format(uri=uri))
    total_hits = requests.get("{uri}&filter_path=hits.total".format(uri=uri)).json()["hits"]["total"]

    # start = time.time()
    if total_hits > 0:
        request = requests.post("{uri}&filter_path=hits.hits._source".format(uri=uri), json.dumps(post_request))
        repeat_timeout = 0
        while request.status_code != 200 and repeat_timeout < 10:
            time.sleep(1)
            # we don't want to repeat forever
            repeat_timeout += 1
            print("Reponse not 200: {resp}".format(resp=request.status_code))
            request = requests.post("{uri}&filter_path=hits.hits._source".format(uri=uri), json.dumps(post_request))
        if request.status_code == 200:
            results = []
            if total_hits < post_request["size"]:
                results = moulinette_json(request.json())
                hits = total_hits
            else:
                hits = post_request["from"] + post_request["size"]
                while hits < total_hits:
                    if hits % (post_request["size"] * 100) == 0:
                        print("{date}: Hit it again, {hits} treated already".format(
                            date=date,
                            hits=hits))
                        # end = time.time() - start
                        # print("It's been {time}".format(time=time.strftime("%H:%M:%S", time.gmtime(end))))
                    post_request["from"] = post_request["from"] + post_request["size"]
                    request = requests.post(uri, json.dumps(post_request))
                    time.sleep(1)
                    results.extend(moulinette_json(request.json()))
                    # time.sleep(0.05) -> the api already throttles the requests? it's already slow to answer,
                    # this sleep is not required
                    hits += post_request["size"]
                    # we should save every 100000 to avoid problems saving the file or other problems
                    if hits % 100000 == 0:
                        save_results(results, "results_{date}_{i}".format(date=date,
                                                                          i=hits))
                        save_total_hits_per_date_name = "hits_{date}".format(date=date)
                        with open(save_total_hits_per_date_name, "w") as f:
                            f.write("Total hits: ")
                            f.write(str(total_hits))
                            f.write("\nHits done: ")
                            f.write(str(hits))
                        results = []

            post_request["from"] = 0
            print("Hits treated {h} for date{date}".format(h=hits, date=date))
        else:
            print("Problem with the request results")
            print(request)


if __name__ == "__main__":
    """                                                                                                                                                      
        This aims to get CI information on kolla-ansible deployments through logstash.openstack.org                                                          
    """
    logging.basicConfig(level=logging.DEBUG)
    from_element = 0
    size = 1000
    print("We're gonna get some Openstack CI info!")
    post_request = {
        "from": from_element,
        "size": size
    }

    uris = get_log_index_uris()
    processes = []
    for uri in uris:
        process = Process(target=get_info_for_one_uri, args=(uri, post_request))
        process.start()
        time.sleep(0.3)
        processes.append(process)
    for p in processes:
        p.join()


