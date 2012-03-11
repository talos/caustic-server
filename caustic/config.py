from ConfigParser import SafeConfigParser
import sys
import uuid

if len(sys.argv) != 2:
    print """
Caustic server must be invoked with a single argument, telling it
which mode from `config.ini` to use:

python caustic/server.py <MODE>

Look at `config.ini` for defined modes. Defaults are `production`,
`staging`, and `test`."""
    exit(1)

MODE = sys.argv[1]
PARSER = SafeConfigParser()

if not len(PARSER.read('config.ini')):
    print "No config.ini file found in this directory.  Writing a config..."

    for mode in ['production', 'staging', 'test']:
        PARSER.add_section(mode)
        PARSER.set(mode, 'db_name', "caustic_%s" % mode)
        PARSER.set(mode, 'db_port', '27017')
        PARSER.set(mode, 'db_host', 'localhost')
        PARSER.set(mode, 'template_dir', './templates')
        PARSER.set(mode, 'cookie_secret', str(uuid.uuid4()))
        PARSER.set(mode, 'json_git_dir', "%s.jsongit" % mode)
        PARSER.set(mode, 'recv_spec', 'ipc://caustic:1')
        PARSER.set(mode, 'send_spec', 'ipc://caustic:0')

    try:
        conf = open('config.ini', 'w')
        PARSER.write(conf)
        conf.close()
    except IOError:
        print "Could not write config file to `config.ini`, exiting..."
        exit(1)

DB_NAME = PARSER.get(MODE, 'db_name')
DB_PORT = int(PARSER.get(MODE, 'db_port'))
DB_HOST = PARSER.get(MODE, 'db_host')
COOKIE_SECRET = PARSER.get(MODE, 'cookie_secret')
RECV_SPEC = PARSER.get(MODE, 'recv_spec')
SEND_SPEC = PARSER.get(MODE, 'send_spec')
JSON_GIT_DIR = PARSER.get(MODE, 'json_git_dir')
TEMPLATE_DIR = PARSER.get(MODE, 'template_dir')
