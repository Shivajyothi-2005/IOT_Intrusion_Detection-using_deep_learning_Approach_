import urllib.request, json, urllib.error

def post_json(url, obj, timeout=30):
    data = json.dumps(obj).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8')
    except urllib.error.HTTPError as he:
        body = he.read().decode('utf-8', errors='ignore') if he.fp else ''
        return f'HTTPError {he.code}: ' + body
    except Exception as e:
        return 'ERR:' + repr(e)

server = 'http://127.0.0.1:8001'

if __name__ == '__main__':
    dev = {'device_id':'linux-laptop-01','name':'My Linux Laptop','ip_address':'192.168.1.15','device_type':'Laptop'}
    print('POST /api/devices ->')
    print(post_json(server + '/api/devices', dev))

    flow = {
        'device_id':'linux-laptop-01',
        'src_ip':'192.168.1.15',
        'dst_ip':'192.168.1.1',
        'src_port':50130,
        'dst_port':80,
        'protocol':6,
        'flow_duration':0.05,
        'packet_count':850,
        'byte_count':54400,
        'tcp_flags_syn':1,
        'tcp_flags_ack':0,
        'tcp_flags_rst':0,
        'tcp_flags_fin':0
    }
    print('POST /api/report-flow ->')
    print(post_json(server + '/api/report-flow', flow))
