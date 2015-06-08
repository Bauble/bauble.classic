#!/bin/bash

PROBLEMS=''
if ! gettext --version >/dev/null 2>&1; then
    PROBLEMS="$PROBLEMS gettext"
fi
if ! python -c 'import gtk' >/dev/null 2>&1; then
    PROBLEMS="$PROBLEMS pygtk"
fi
if ! git help >/dev/null 2>&1; then
    PROBLEMS="$PROBLEMS git"
fi
if ! virtualenv --help >/dev/null 2>&1; then
    PROBLEMS="$PROBLEMS virtualenv"
fi
if ! xslt-config --help >/dev/null 2>&1; then
    PROBLEMS="$PROBLEMS libxslt1-dev"
fi
PYTHONHCOUNT=$(find /usr/include/python* /usr/local/include/python* -name Python.h 2>/dev/null | wc -l)
if [ "$PYTHONHCOUNT" = "0" ]; then
    PROBLEMS="$PROBLEMS python-all-dev"
fi

if [ "$PROBLEMS" != "" ]; then
    echo please first solve the following dependencies:
    echo '     (package names are ubuntu/debian, YMMV).'
    echo $PROBLEMS
    exit 1
fi

if [ -d $HOME/Local/github/Bauble/bauble.classic ]
then
    echo "bauble checkout already in place"
    cd $HOME/Local/github/Bauble/bauble.classic
else
    mkdir -p $HOME/Local/github/Bauble >/dev/null 2>&1
    cd $HOME/Local/github/Bauble
    git clone https://github.com/Bauble/bauble.classic
    cd bauble.classic
fi

if [ $# -ne 0 ]
then
    git checkout bauble-$1
else
    git checkout bauble-1.0
fi

mkdir $HOME/.virtualenvs >/dev/null 2>&1
virtualenv $HOME/.virtualenvs/bacl --system-site-packages
find $HOME/.virtualenvs/bacl -name "*.pyc" -execdir rm {} \;
find $HOME/.virtualenvs/bacl -name "*.pth" -execdir rm {} \;
mkdir $HOME/.virtualenvs/bacl/share >/dev/null 2>&1
mkdir $HOME/.bauble >/dev/null 2>&1
source $HOME/.virtualenvs/bacl/bin/activate

pip install setuptools pip --upgrade

python setup.py build
python setup.py install
mkdir $HOME/bin 2>/dev/null
cat <<EOF > $HOME/bin/bauble
#!/bin/bash

GITHOME=$HOME/Local/github/Bauble/bauble.classic/
source \$HOME/.virtualenvs/bacl/bin/activate

BUILDANDEND=0
while getopts us: f
do
  case \$f in
    u)  cd \$GITHOME
        BUILDANDEND=1;;
    s)  cd \$GITHOME
        git checkout bauble-\$OPTARG || exit 1
        BUILDANDEND=1;;
  esac
done

if [ "\$BUILDANDEND" == "1" ]
then
    git pull
    python setup.py build
    python setup.py install
    exit 1
fi

bauble
EOF
chmod +x $HOME/bin/bauble
