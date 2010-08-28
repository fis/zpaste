#! /usr/bin/env perl

use strict;
use warnings;

# settings

use constant DATADIR => '/space/www/data/zpaste';
use constant BASEURL => 'http://p.zem.fi/';

use constant HL_LANGS => '/usr/share/highlight/langDefs';
use constant HL_THEMES => '/usr/share/highlight/themes';

=head1 NAME

zpaste-hl.cgi - zpaste script for syntax highlighting

=head1 SYNOPSIS

Visible URL:

  http://www.example.com/x.y[&theme=z&noln=1]

Underlying URL:

  http://www.example.com/zpaste-hl.cgi?name=x&lang=y \
    [&theme=z&noln=1]

=head1 DESCRIPTION

This script is used to provide syntax highlighting for pastes.  The
script expects to be called via Apache rewriting module (as seen in
the B<SYNOPSIS> section), and the URLs generated when user switches
languages or themes are written under this assumption.

The arguments accepted this script are the following:

=over 4

=item I<name> (required)

Name of the paste to syntax-highlight.

=item I<lang> (required)

Language used for syntax-highlighting.

=item I<theme> (optional)

Color theme.

=item I<noln> (optional)

If set, omits the line numbers.

=back

=cut

use CGI;
use File::Spec::Functions;
use highlight;

# parse parameters

my $q = CGI->new;
print $q->header(-type => 'application/xhtml+xml', -charset => 'utf-8');

my $name = $q->param('name') || 'does.not.exist';
my $lang = $q->param('lang') || 'undefined';
my $theme = $q->param('theme') || 'emacs';

my $noln = $q->param('noln') ? 1 : 0;

$name =~ s/[^A-Za-z0-9_-]//g;

err("non-existent paste: $name") unless -r catfile(DATADIR, $name);
err("unsupported language: $lang") unless -r catfile(HL_LANGS, $lang.'.lang');
err("unsupported theme: $theme") unless -r catfile(HL_THEMES, $theme.'.style');

# construct the syntax highlight engine

my $cg = highlightc::CodeGenerator_getInstance($highlightc::XHTML);

$cg->initTheme(catfile(HL_THEMES, $theme.'.style'));
$cg->loadLanguage(catfile(HL_LANGS, $lang.'.lang'));

$cg->setPrintLineNumbers($q->param('noln') ? 0 : 1);
$cg->setIncludeStyle(1);
$cg->setEncoding('utf-8');
$cg->setTitle($name);

# generate the output, split to pieces

my ($out_prestyle, $out_hdr, $out_body, $out_ftr);

eval {
    my $t = $cg->generateStringFromFile(catfile(DATADIR, $name));

    $t =~ m{^(.*)(</style>.*)$}s or die "can't find end of style";
    ($out_prestyle, $t) = ($1, $2);

    $t =~ m{^(.*<body class="hl">)(.*)$}s or die "can't find start of body";
    ($out_hdr, $t) = ($1, $2);

    $t =~ m{^(.*)(</body>.*)$}s or die "can't find end of body";
    ($out_body, $out_ftr) = ($1, $2);
};
err("highlight output error: $@") if $@;

highlightc::CodeGenerator_deleteInstance($cg);
$cg = undef;

$out_prestyle =~ s{font-family:'Courier New';}{};
$out_prestyle =~ m/pre.hl\s*{([^}]*)}/;
my $defcss = $1;
$defcss =~ m/color:(#[0-9a-f]+)/;
my $defcolor = $1;

# create the output stuff

print $out_prestyle;

print "pre.hl, div.menu { font-family: \"DejaVu Sans Mono\", monospace; }\n";
print "div.menu {$defcss}\n";
print "div.menu { border-bottom: 1px solid $defcolor; }\n";
print "span.menulabel { padding-left: 2ex; }\n";
print "span.menulabel a { color: $defcolor; }\n";

print $out_hdr;

gen_menu();

$out_body =~ s{(<span class="hl line"> *\d+) (</span>)}{$1\t$2}g;
print $out_body;

print $out_ftr;

# helper subs

sub err
{
    my $reason = shift;
    print "XXX = $reason\n";
    exit 0;
}

sub gen_menu
{
    my $url = BASEURL.$name;

    print "<script type=\"text/javascript\">\n";
    print "function upd() {";
    print "  var l = document.getElementById('menulang');\n";
    print "  var t = document.getElementById('menutheme');\n";
    print "  var n = document.getElementById('menunoln');\n";
    print "  if (l.selectedIndex &lt; 0 || t.selectedIndex &lt; 0) return;\n";
    print "  var url = '$url.' + l.options[l.selectedIndex].value + '?theme=' + t.options[t.selectedIndex].value;\n";
    print "  if (n.checked) url += '&amp;noln=1';\n";
    print "  location.href = url;\n";
    print "}\n";
    print "</script>\n";

    my @langs = sort map { m{([0-9a-z_-]+).lang$} } glob catfile(HL_LANGS, '*');
    my @themes = sort map { m{([0-9a-z_-]+).style$} } glob catfile(HL_THEMES, '*');

    print "<div class=\"menu\">\n";

    print "<span class=\"menulabel\">Language: </span>\n";
    print "<select id=\"menulang\" onchange=\"upd();\">\n";
    foreach my $l (@langs)
    {
        printf("<option value=\"%s\"%s>%s</option>\n",
               $l, ($l eq $lang ? " selected=\"true\"" : ""), $l);
    }
    print "</select>\n";

    print "<span class=\"menulabel\">Colors: </span>\n";
    print "<select id=\"menutheme\" onchange=\"upd();\">\n";
    foreach my $t (@themes)
    {
        printf("<option value=\"%s\"%s>%s</option>\n",
               $t, ($t eq $theme ? " selected=\"true\"" : ""), $t);
    }
    print "</select>\n";

    my $noln_checked = '';
    $noln_checked = ' checked="true"' if $noln;
    print "<span class=\"menulabel\">Hide line numbers: </span>\n";
    print "<input id=\"menunoln\" type=\"checkbox\"$noln_checked onchange=\"upd();\" />\n";

    print "<span class=\"menulabel\"><a href=\"$url.bin\">{download}</a></span>\n";

    print "</div>\n";
}
