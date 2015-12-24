BASEDIR=$(dirname $0)
# Install wtforms-admin to our lib/ directory, using our local source tree
pip install -t $BASEDIR/lib/ $BASEDIR/../.. wtforms_appengine
# Now run our server
dev_appserver.py $BASEDIR/app.yaml
