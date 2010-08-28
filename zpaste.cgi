#! /usr/bin/env perl

use strict;
use warnings;

# settings

use constant KEY => 'zi8ahkoobahko,xaefeetuphei6eaCee';
use constant DATADIR => '/space/www/data/zpaste';
use constant METADIR => '/space/www/data/zpaste/.web';
use constant METASUFFIX => '.meta';
use constant BASEURL => 'http://p.example.com/';

# documentation

=head1 NAME

zpaste.cgi - zpaste script for accepting paste requests

=head1 SYNOPSIS

  https://www.example.com/zpaste.cgi (POST)

=head1 DESCRIPTION

This scripts accepts a paste request from the command-line client
(B<zpaste>).  The "form" submitted by B<zpaste> has the following
fields:

=over 4

=item I<key> (required)

The pre-shared authentication key: an arbitrary string.  Just make
sure the C<KEY> constants in both this script and the B<zpaste> client
match.

=item I<data> (required, unless I<del> is set)

Contents of the paste.  In most cases, this should (and has to) be a
file attachment field, the contents of which will be directly written
as the contents of the paste.  The single exception is if I<link> is
set: in that case, this field needs to be a regular plain old text
field, containing the URL to redirect to.

=item I<name> (optional, unless I<del> is set)

Name of the paste.  If not specified, a random name will be generated.

=item I<link> (optional, boolean)

If set, the paste is instead a link to redirect to.

=item I<force> (optional, boolean)

If set, a paste with the same name than an existing one overwrites the
old one.  If not set, a duplicate name is an error.

=item I<del> (optional, boolean)

If set, deletes the named paste instead of adding a new one.

=back

=cut

use CGI;
use File::Spec::Functions;
use Fcntl;

use SDBM_File;
#use GDBM_File;

# CGI setup

my $q = CGI->new;

# check for authentication

my $key = $q->param('key') || '';
if ($key ne KEY)
{
    print $q->header(-type => 'text/plain', -charset => 'utf-8', -status => '403');
    print "invalid authentication key\n";
    exit;
}

print $q->header(-type => 'text/plain', -charset => 'utf-8');

# attach to the rewrite mapping db

my $rewritedb = catfile(DATADIR, 'rewrite.db');
my %rewrites;

tie %rewrites, 'SDBM_File', $rewritedb, O_RDWR|O_CREAT, 0644;
# tie %rewrites, 'GDBM_File', $rewritedb, &GDBM_WRCREAT, 0644;

unless (tied %rewrites)
{
    print "unable to attach: $rewritedb: $!";
    exit;
}

# decide on file name

my $name = $q->param('name');

if ($name)
{
    $name =~ s/[^a-zA-Z0-9_-]//g;
}
else
{
    # invent a random non-existing name
  RANDNAME:
    foreach my $len (4 .. 8)
    {
        for (my $count = 10**$len; $count > 0; $count--)
        {
            $name = randname($len);
            last RANDNAME unless -e $name || $rewrites{$name};
        }
    }

    if (!$name || -e $name)
    {
        print "unable to invent a name\n";
        exit;
    }
}

# for pre-existing names, abort or wipe the old

if ($rewrites{$name})
{
    if ($q->param('force') || $q->param('del'))
    {
        delete $rewrites{$name};
    }
    else
    {
        print "link '$name' exists already\n";
        exit;
    }

    if ($q->param('del'))
    {
        print "link '$name' deleted\n";
        exit;
    }
}
elsif (-e catfile(DATADIR, $name))
{
    if ($q->param('force') || $q->param('del'))
    {
        unlink catfile(DATADIR, $name), catfile(METADIR, $name.METASUFFIX);
    }
    else
    {
        print "paste '$name' exists already\n";
        exit;
    }

    if ($q->param('del'))
    {
        print "paste '$name' deleted\n";
        exit;
    }
}
elsif ($q->param('del'))
{
    print "paste '$name' does not exist\n";
    exit;
}

# make sure there's some data in the request

my $data = $q->param('data');
unless ($data)
{
    print "request data field empty\n";
    exit;
}

# handle link-redirection "pastes"

if ($q->param('link'))
{
    $rewrites{$name} = $data;
    untie %rewrites;
    print BASEURL, $name, "\n";
    exit;
}

# write paste metafile if necessary

my $type = $q->param('type');

if ($type)
{
    my $metafile = catfile(METADIR, $name.METASUFFIX);
    open my $meta, '>:utf8', $metafile;
    unless ($meta)
    {
        print "unable to write: $metafile: $!\n";
        exit;
    }
    chmod 0644, $metafile;

    print $meta "Content-Type: $type\n";

    close $meta;
}

# write the paste contents to file

my $in = $q->upload('data');
unless ($in)
{
    print "request data field not a file\n";
    exit;
}

my $datafile = catfile(DATADIR, $name);
open my $out, '>:raw', $datafile;
unless ($out)
{
    print "unable to write: $datafile: $!\n";
    exit;
}
chmod 0644, $datafile;

my $buf;
print $out $buf while read($in, $buf, 65536) > 0;

close $in;
close $out;

# return a link to the created paste

print BASEURL, $name, "\n";

# helper subs

sub randname
{
    my $len = shift;
    return join('', map { my $r = int(rand(36)); $r < 10 ? chr(0x30+$r) : chr(87+$r) } (1 .. $len));
}
