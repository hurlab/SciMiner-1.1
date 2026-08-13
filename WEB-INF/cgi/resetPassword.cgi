#! /usr/bin/perl
#******************************************************************************
#
#                resetPassword.cgi for SciMiner on the web
#
#  Created 	: 08/13/2026  (legacy password migration, phase D)
#  Desc		: Landing page for the reset link issued by lostPassword.cgi.
#
#  Flow
#  ---------------------------------------------------------------------------
#    GET  ?token=...                    -> validate the token, show the form
#    POST token + newPass1 + newPass2   -> validate again, set the new password
#
#  The token is never stored; only its SHA-256 is, so this page hashes the
#  incoming token and looks that up. A token is single-use and expires (the
#  expiry is set by lostPassword.cgi).
#
#  On success the account is switched to hash-only auth: `password_hash` is
#  written and `passCode` is blanked, which removes this account from the
#  cleartext fallback in SciMiner_email_password_check.
#******************************************************************************
BEGIN {
push (@INC, "/home/hurlab/apache-tomcat-9.0.37/webapps/SciMiner1.1/annotation/SciMinerDB/Modules/");
}

# ----------------------------------------------------------------------------
#  Load required modules
# ----------------------------------------------------------------------------
use Annotation::basicIO;
use Annotation::SciMiner;
use CGI qw(:standard);
use CGI::Debug;
use DBI;
use Digest::SHA qw(sha256_hex);
use SciMiner::Security qw(hash_password);
#use warnings;
use strict;

$CGI::LIST_CONTEXT_WARN = 0;

#  Minimum length for a newly chosen password.
my $MIN_PASSWORD_LENGTH = 8;

#here's a stylesheet incorporated directly into the page
my  $newStyle=<<END;
<!--
body {
    margin-left: 10px;
}
-->
END


# ----------------------------------------------------------------------------
#  Load working environment for ANNOTATION
# ----------------------------------------------------------------------------
my %annoENV = anno_environmental_file_open ( );
my $annoBaseDir = $annoENV{ANNOPath};

my $query = new CGI;


#------------------------------------------------------------------------------
#  Initialize the CGI page
#------------------------------------------------------------------------------
print header;
print $query->start_html(-title=>'SciMiner Password Reset',
                        -author=>'InformaticsTools@gmail.com',
                        -meta=>{'keywords'	=>	'Junguk Hur SciMiner text mining text-mining bioinformatics',
                                'copyright'	=>	'copytight 2006-8 Junguk Hur'},
                        -BGCOLOR=>'#EAF4F4',
                        -style=>{-src=>['mm_health_nutr.css'], -code=>$newStyle}
                        );


#------------------------------------------------------------------------------
#	Main
#------------------------------------------------------------------------------
my $token		= param("token");
$token			= '' unless (defined $token);
$token			=~ s/^\s+|\s+$//g;

#  The token alphabet is [A-Za-z0-9] (SciMiner::Security::generate_token), so
#  anything else is malformed and is rejected before it reaches the database.
unless ($token =~ /\A[A-Za-z0-9]{16,128}\z/)
{	print_invalid();
	print_end_html();
	exit;
}

my ($userID, $userEmail) = lookup_token (\%annoENV, $token);

unless (defined $userID)
{	print_invalid();
	print_end_html();
	exit;
}

if (defined param("newPass1"))
{	my $newPass1	= param("newPass1");
	my $newPass2	= param("newPass2");
	$newPass2		= '' unless (defined $newPass2);

	if ($newPass1 ne $newPass2)
	{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>The two passwords are not identical. Please try again.</b></p>";
		print_form($token);
	}
	elsif (length($newPass1) < $MIN_PASSWORD_LENGTH)
	{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>Please choose a password of at least $MIN_PASSWORD_LENGTH characters.</b></p>";
		print_form($token);
	}
	else
	{	my $status	= apply_new_password (\%annoENV, $userID, $newPass1);
		if ($status == 1)
		{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>Your SciMiner password has been changed.</b><br><br>".
			      "You can now sign in as $userEmail with your new password.</p>";
		}else
		{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>Sorry -- the password could not be changed. Please request a new reset link, or contact $annoENV{AdminEmail}.</b></p>";
		}
	}
}else
{	print "<p class=\"titleBarName1\"><b>Choose a new password for $userEmail.</b></p>";
	print_form($token);
}

print_end_html();
exit;


#------------------------------------------------------------------------------
#	Sub-routines
#------------------------------------------------------------------------------


sub print_end_html
{   print end_html;
}


sub print_invalid
{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>This password reset link is invalid or has expired.</b><br><br>".
	      "Reset links can be used once and are valid for a limited time.<br><br>".
	      "<a href=\"lostPassword.cgi\">Request a new one</a>.</p>";
}


sub print_form
{	my $formToken	= shift;
	print "<form name=\"form1\" action=\"resetPassword.cgi\" method=\"POST\" enctype=\"multipart/form-data\">
			<input type='hidden' name='token' value=\"$formToken\">
			New password (at least $MIN_PASSWORD_LENGTH characters) : <INPUT TYPE='password' NAME='newPass1' size=\"35\"><br><br>
			New password (repeat here) : <INPUT TYPE='password' NAME='newPass2' size=\"35\"><br><br>
	       <input type='submit' name=\"formSubmit\" value=\"Set new password\">
		   </form>
		   <br><br>";
}


sub db_handle
{	my $annoENVRef	= shift;

    my $SciMinerDB  = "DBI:mysql:database=".$$annoENVRef{DB} || return (undef);
    my $username    = $$annoENVRef{username} || return (undef);
    my $password    = $$annoENVRef{password} || return (undef);

    return DBI->connect($SciMinerDB, $username, $password, {PrintError => 0});
}


#  Resolve a raw token to (userID, email), or an empty list when the token is
#  unknown, already used, or past its expiry. NOW() is evaluated by MySQL so the
#  comparison does not depend on the CGI process clock.
sub lookup_token
{	my $annoENVRef	= shift;
	my $rawToken	= shift;

	my $dbh			= db_handle($annoENVRef) || return ();
	my $tokenHash	= sha256_hex($rawToken);

	my $sth			= $dbh->prepare("SELECT userID, email FROM user WHERE password_reset_token = ? AND password_reset_expires IS NOT NULL AND password_reset_expires > NOW() AND suspended = 0");
	$sth->execute($tokenHash) || return ();
	my @row			= $sth->fetchrow_array;

	return () unless ((defined $row[0]) && ($row[0] ne ''));
	return ($row[0], $row[1]);
}


#  Write the new bcrypt hash, blank the cleartext column, and burn the token in
#  one statement so a reset cannot be replayed.
sub apply_new_password
{	my $annoENVRef	= shift;
	my $userID		= shift;
	my $newPassword	= shift;

	my $passwordHash = eval { hash_password($newPassword) };
	return (0) if ((! defined $passwordHash) || ($passwordHash eq ''));

	my $dbh			= db_handle($annoENVRef) || return (0);

	my $upd			= $dbh->prepare("UPDATE user SET password_hash = ?, passCode = '', password_reset_token = NULL, password_reset_expires = NULL WHERE userID = ?");
	my $rows		= $upd->execute($passwordHash, $userID);

	return (0) unless ((defined $rows) && ($rows ne '0E0'));
	return (1);
}
