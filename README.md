Introduction
============

*zpaste* is a simple, single-user (or not-too-many-user)
pastebin/tinyurl hybrid, in case you want something a bit more
tweakable than the myriad of web services around.

Main selling points:

* Can specify `Content-Type:` to handle binaries somewhat.
* Does the job of both pastebin and tinyurl.
* Allow meaningful names as well as update/delete of past pastes.

Usage
=====

    ... | zpaste [name]
    zpaste --link http://example.com/ [name]

The first command above pastes the contents of standard input.  A link
to the generated paste is written to standard output.  The optional
argument *name* gives the name (alphanumerics, underscore and dash
only); if not provided, a random name is used.

The second form makes a tinyurl-style address redirection entry to the
provided URL.

Command line options accepted by the command:

* **--force**: If specified, existing pastes/links are overwritten;
  otherwise, a duplicate name is an error.
* **--del**: Instead of adding a new paste, delete an existing one.
  The *name* argument is required in this case.

Installation
============

Requirements
------------

You will need an Apache server, most likely one you can configure
freely.  Some bits of the system are done with `mod_rewrite`, and
others with `mod_alias`, and you'll also need `mod_cern_meta` loaded
for the content type specifying to work.  If your server is very
friendly with overrides, you may be able to get things rolling with
just suitable `.htaccess` files.

You will also need Perl, and the following heap of Perl modules.

The paste submission script needs `LWP`'s HTTP client, and if you want
to put the paste submission script behind HTTPS (you *really* should),
you'll need `IO::Socket::SSL` too (Debian/Ubuntu:
`libio-socket-ssl-perl`).

The server-side CGI script for accepting pastes needs a DBM library.
By default, `SDBM_File` (which is part of the core Perl distribution)
is used, but it is possible to use GDBM too.  In this case, though,
your Apache will need to be built with GDBM support.

The syntax-highlight support script needs the Perl interface of
[this](http://www.andre-simon.de/) syntax highlighting machine
(Debian/Ubuntu: `libhighlight-perl`).

Instructions
------------

The instructions here assume you will dedicate a single vhost for the
publicly accessible side, and stick the server-side paste accepting
script to another HTTPS-enabled vhost on the same server.  If your
setup differs from this, adapt accordingly.

### Step 1: decide where to put the stuff

You will need one data directory that is writable by the user/group
the server-side scripts run as.  This probably should not be under the
`DocumentRoot` of your server.  Let's call this directory *DATADIR*.
The default settings of the scripts use `/space/www/data/zpaste`.

You will also need to put the server-side script itself somewhere.
Let's call the absolute path to this script *SCRIPTPATH*.  By default,
this is in `/space/www/data/zpaste.cgi`.  This should be visible to
the world using the address *SCRIPTURL*; by default,
`https://example.com/zpaste.cgi`.

Finally, you will need to put the web server's document root
somewhere; let's call this directory *WEBDIR*.  The default value here
is `/space/www/zpaste`.  Make this directory accessible as *WEBURL*;
by default, `http://p.example.com/`.

### Step 2: edit the configuration sections of the scripts

In the command-line client **zpaste**, you will need to change:

* **KEY**: set to arbitrary string used for shared-secret authentication.
* **SCRIPT**: set to *SCRIPTURL* defined in Step 1.

In the server-side **zpaste.cgi**, you will need to change:

* **KEY**: set to the same arbitrary string as you did above.
* **DATADIR**: set to *DATADIR* of Step 1.
* **METADIR**: set to *DATADIR*/.web, unless you change `mod_cern_meta` configs.
* **METASUFFIX**: set to `.meta`, unless you change `mod_cern_meta` configs.
* **BASEURL**: set to *WEBURL* of Step 1.

Finally, in the highlight script **zpaste-hl.cgi**, you will need to change:

* **DATADIR**: set like in **zpaste.cgi**.
* **BASEURL**: set like in **zpaste.cgi**.
* **HL_LANGS**: set to highlight engine's language defs; default will work in Debian/Ubuntu.
* **HL_THEMES**: set to highlight engine's themes; default will work in Debian/Ubuntu.

### Step 3: putting stuff in place

Make the directories *DATADIR* and *DATADIR*/.web, and set their
permissions so that the server-side paste-accepting script can make
new files in both.

Put the edited **zpaste.cgi** to *SCRIPTPATH*.

Make the *WEBDIR* directory, set permissions so that the server can
read it.  Put some sort of `index.html` there if you want.  Make the
subdirectory *WEBDIR*/hl, and put the edited **zpaste-hl.cgi** there.

Put the edited **zpaste** to somewhere in your `$PATH`.

### Step 4: server configuration editing

Into the HTTPS-enabled vhost, put the line:

    ScriptAlias /zpaste.cgi *SCRIPTPATH*

If your *SCRIPTURL* has a subdirectory in it, remember to include that
in the first argument.

The *WEBURL* vhost (`p.example.com`) should look something like this;
substitute the correct paths to places marked {{LIKE THIS}}.

    <VirtualHost 1.2.3.4:80>
        ServerName p.example.com
        ServerAdmin webmaster@example.com
        ServerSignature On

        DocumentRoot {{WEBDIR}}

        RewriteEngine On
        RewriteMap zpastemap dbm=sdbm:{{DATADIR}}/rewrite.db
        RewriteCond %{REQUEST_URI} ^/([a-zA-Z0-9_-]+)$
        RewriteCond ${zpastemap:%1} !=""
        RewriteRule ^/([a-zA-Z0-9_-]+)$ ${zpastemap:$1} [L,R=302]
        RewriteRule ^/([a-zA-Z0-9_-]+)\.bin$ /$1 [PT,T=application/octet-stream]
        RewriteRule ^/([a-zA-Z0-9_-]+)\.([a-z0-9]+)$ /hl/zpaste-hl.cgi?name=$1&lang=$2 [NS,QSA]

        AliasMatch ^(/[a-zA-Z0-9_-]+)$ {{DATADIR}}$1

        <Directory {{WEBDIR}}>
            Order Allow,Deny
            Allow from all
        </Directory>

        <Directory {{WEBDIR}}/hl>
            SetHandler cgi-script
            Options ExecCGI
        </Directory>

        <Directory {{DATADIR}}>
            Order Allow,Deny
            Allow from all
            MetaFiles on
        </Directory>

        CustomLog /whatever/access.log combined
        ErrorLog /whatever/error.log
        LogLevel warn
    </VirtualHost>
