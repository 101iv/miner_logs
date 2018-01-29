#!/usr/bin/python
# -*- coding: cp1251 -*-

import os, re, json
from datetime import datetime


#analyze1 - ����� �������� ��� ������� ����, �� ������� �������� �������� ������ ��� ���� ��� ���/���.
#analyze2 - ����� �������� ��� ������ ����������, �� ������� �������� �������� ������ � ���������� ��� �� ���� �����.
# ������� analyze2 ����� ���������, ��� ������� �� analyze1


# ������ ���� � ����� 01/26/18-03:47:05
DATA_FORMAT = '%m/%d/%y-%H:%M:%S'

# ����� � ��������� ������
DIR_LOGS = "logs/"

# ����� ��� ������������� ������ � ������� json
DIR_DATA = "data/"

# ����� ��� ����������� - ��������� ����� ���������� � ��������, ������ ���� .html
HTML_RESULTS = "html_results/"

# ������������ ������ �� ����� ��� ����� ������ �� DIR_DATA 
REWRITE_DATA = 0

# ������ ������ ��� �����, ������������ ������� ������ ��������� ������� - MIN_TIME_JOB �����
MIN_TIME_JOB = 1  # 1 ���

# ���������� ��������� � ����, ��������� ���� �� ����� ���������� ���������� �� ����, ���� ���������� �������� �������, �� ������ ����� ��������������
GPU_COUNT = 8

# ������ ��� �������� ���������� ��� - PERIOD1 ������
PERIOD1 = 300



# �� ����� � ������ �������� ����� ������, ������������� �� ������ � �����
def get_files_names():
    arr_names = os.listdir(DIR_LOGS)
    return sorted(arr_names)


def read_file(file):
    f = open(file, "r")
    res = f.read()
    f.close()
    return res


def write_file(data, name):
    f = open(name, "w")
    f.write(data)
    f.close()


# �� ����� �������� ����� ���������� ����, gpu, ������ ������ ����
def get_data_from_log(f_name):
    res = read_file(DIR_LOGS + f_name)

    re_1 = re.compile(  # ETH: 01/26/18-03:47:05 - SHARE FOUND - (GPU 7)
        r'ETH: (.+?) - SHARE FOUND - \(GPU (.+?)\)\n')  # ,re.DOTALL | re.MULTILINE
    m_shares = re.findall(re_1, res)

    re_1 = re.compile(  # ETH: 01/26/18-03:47:05 - SHARE FOUND - (GPU 7)
        r'(.+?)	.+?-epsw x (.+?)\n')  # ,re.DOTALL | re.MULTILINE
    m_config = re.findall(re_1, res)

    re_2 = re.compile(  # ETH: 01/26/18-03:47:05 - SHARE FOUND - (GPU 7)
        r'WATCHDOG: (.+?) hangs in OpenCL call, exit')  # ,re.DOTALL | re.MULTILINE
    m_err = re.findall(re_2, res)

    if m_err == []:
        error = "��� ������ GPU"
    else:
        error = "������: %s" % m_err[0]

    try:
        data = json.dumps([m_shares, m_config[0][1], error], sort_keys=True, indent=1)
        write_file(data, DIR_DATA + f_name + ".json")
        print("�������� ����� � ����� %s" % f_name)
        return m_shares, m_config[0][1], error
    except:
        print("������ � ����� %s" % f_name)
        exit()


# ����� ������� ������
def get_ready_data(f_name):
    res = read_file(DIR_DATA + f_name + ".json")
    data = json.loads(res)

    # print("������ ������� �� ����� data")
    return data


def format_br_before(data):
    words = ["-tt", "-cclock", "-mclock", "-powlim", "-cvddc", "-mvddc"]
    for w in words:
        data = re.sub(w, "<br>" + w, data)
        if w == "-cclock": data = re.sub(w, "<br>" + w, data)
    return data


def found_config_for_gpu(num_gpu, config):
    # config = '-asm 1 -dcri 5 -ttli 80 -tt 65,65,65 -cclock 1150  -mclock 2150 -powlim 38 -cvddc 900 -mvddc 925 '
    all_values = []
    for name_conf in ["-cclock ", "-mclock ", "-cvddc ", "-mvddc ", "-tt "]:
        res0 = re.sub("-", "\n-", config)
        res = re.findall("%s(.+)" % name_conf, res0)
        try:
            res[0] = re.sub(" ", "", res[0])
        except:
            res.append([""])
        value = ""

        try:
            res = res[0].split(",")
        except:
            value = ""
        if len(res) > 1:
            try:
                value = res[num_gpu]
            except:
                value = ""
        else:
            value = res[0]
        all_values.append(value)

    return all_values[0], all_values[1], all_values[2], all_values[3], all_values[4]


def csv_shares_gpus(f_name, data, period):
    gpu = [0 for c in range(0, GPU_COUNT)]
    # period = datetime.strptime(str(period),"%H")
    time_result = datetime.strptime(data[0][0], DATA_FORMAT)
    for time, num_gpu in data:
        time = datetime.strptime(time, DATA_FORMAT)
        tt = time - time_result
        if tt.seconds <= period:
            gpu[int(num_gpu)] = gpu[int(num_gpu)] + 1
        else:
            time_result = time
            s = ""
            for g in gpu:
                s = s + "%s\t" % g
            print(str(time) + "\t", s)
            gpu = [0 for c in range(0, GPU_COUNT)]


def build_gr_all_gpus_one_log(shares, config, error, n):
    gpu = [0 for c in range(0, GPU_COUNT)]
    # ������ �����
    time_begin = datetime.strptime(shares[0][0], DATA_FORMAT)
    time_end = time_begin

    for time, num_gpu in shares:
        time = datetime.strptime(time, DATA_FORMAT)
        gpu[int(num_gpu)] = gpu[int(num_gpu)] + 1
        time_end = time

    time_job = time_end - time_begin
    time_job = time_job.total_seconds() / 3600

    if time_job < MIN_TIME_JOB: return ""

    # ������ ������
    # 'GPU 0','GPU 1','GPU 2','GPU 3','GPU 4','GPU 5','GPU 6','GPU 7'
    gpus = ''
    for g in range(0, GPU_COUNT):
        gpus += "'GPU %s', " % g
    gpus = gpus[:-2]

    # 49.9, 71.5, 106.4, 129.2, 144.0, 176.0, 135.6, 148.5
    count_shares = ''
    num_gpu = 0
    while num_gpu < GPU_COUNT:
        title = found_config_for_gpu(num_gpu, config)
        count_shares += "['%s/%s<br>%s/%s<br>%s', %s], " % (
            title[0], title[1], title[2], title[3], title[4],
            (gpu[num_gpu] / time_job)
        )
        num_gpu += 1

    count_shares = count_shares[:-2]

    config = "<b>����� ������: %s � </b><br><b>%s</b><br>%s" % (round(time_job, 2), error, config)
    config = format_br_before(config)

    middle_html = read_file('html_templates/middle_all_gpus_one_log.html')
    middle_html = middle_html % (config, n, n, time_begin, time_end, gpus, count_shares)
    print("�������� ������ %s" % n)

    return middle_html


def build_gr_all_sh_one_gpu(data):
    yaxis_total_shares = ''
    xaxis_speed = ''
    xaxis_dates = ''
    xaxis_errors = ''
    text_info = ''
    xaxis_conf1 = ''
    xaxis_conf2 = ''
    xaxis_conf3 = ''
    xaxis_conf4 = ''

    for shares, config, error, num_gpu in data:
        time_begin = datetime.strptime(shares[0][0], DATA_FORMAT)
        time_end = time_begin

        total_shares = 0
        error_int = '""'
        for time, n in shares:
            time = datetime.strptime(time, DATA_FORMAT)
            if int(n) == num_gpu: total_shares += 1
            time_end = time

        time_job = time_end - time_begin
        time_job = time_job.total_seconds() / 3600

        if error.find("������: GPU %s" % num_gpu) != -1:
            error_int = 1

        conf1,conf2,conf3,conf4,conf5 = found_config_for_gpu(num_gpu, config)

        text_tooltip = "-tt=%s" %(conf5)
        if time_job >= MIN_TIME_JOB:
            if time_job == 0: time_job = 0.01
            yaxis_total_shares += '["<b>%s</b><br>%s<br>����� ������:%s �", %s], ' % (
                error,text_tooltip, round(time_job,2), total_shares
            )
            xaxis_speed += '%s, ' % (round (total_shares / time_job, 2))
            xaxis_dates += '"%s", ' % time_begin
            xaxis_errors += '%s, ' % (error_int)
            xaxis_conf1 += '%s, ' % conf1
            xaxis_conf2 += '%s, ' % conf2
            xaxis_conf3 += '%s, ' % conf3
            xaxis_conf4 += '%s, ' % conf4

        if error_int ==1:
            text_info += "������ GPU %s=0.00mh/s: %s  (%s/%s  %s/%s  -tt=%s)<br>" % (num_gpu, time_begin,conf1,conf2,conf3,conf4,conf5)

    middle_html = read_file('html_templates/middle_all_shares_one_gpu.html')
    middle_html = middle_html % (
        num_gpu, num_gpu, num_gpu, xaxis_dates, yaxis_total_shares, xaxis_speed,xaxis_errors,
        xaxis_conf1,xaxis_conf2,xaxis_conf3,xaxis_conf4,text_info
    )

    return middle_html

def analyze1():
    f_names = get_files_names()
    res_html = read_file('html_templates/header.html')

    n = 0
    # f_names = ['1515285604_log.txt']
    for f_name in f_names:
        if REWRITE_DATA == True:
            shares, config, error = get_data_from_log(f_name)
        else:
            try:
                shares, config, error = get_ready_data(f_name)
            except:
                shares, config, error = get_data_from_log(f_name)
        # csv_shares_gpus(f_name + "_%ssec.csv" % PERIOD1, sh, PERIOD1)
        if shares != []: res_html += build_gr_all_gpus_one_log(shares, config, error, n)
        n += 1


    res_html += read_file('html_templates/footer.html')
    write_file(res_html, HTML_RESULTS + "all_gpus_one_log.html")


def analyze2():
    f_names = get_files_names()
    res_html = read_file('html_templates/header.html')

    # for num_gpu in range (0, GPU_COUNT):
    for num_gpu in range (7, 8):
        data = []
        # f_names = ['1516963897_log.txt']
        for f_name in f_names:
            print ("��������� %s" % f_name)
            if REWRITE_DATA == True:
                shares, config, error = get_data_from_log(f_name)
            else:
                try:
                    shares, config, error = get_ready_data(f_name)
                except:
                    shares, config, error = get_data_from_log(f_name)
            if shares != []: data.append([shares, config, error, num_gpu])
        res_html += build_gr_all_sh_one_gpu(data)
    res_html += read_file('html_templates/footer.html')

    write_file(res_html, HTML_RESULTS + "all_sh_one_gpu.html")


if __name__ == "__main__":
    analyze1()
    # analyze2()
