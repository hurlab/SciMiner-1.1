#! /usr/bin/perl
#******************************************************************************
#
#                lostPassword.cgi for SciMiner on the web
#
#                                         Written By Junguk HUR
#                                         juhur @ umich . edu
#
#  Created 	: 03/27/2009
#  Desc		: This CGI lets a user request a password RESET LINK.
#
#  2026-08-13 (legacy password migration, phase D)
#  ---------------------------------------------------------------------------
#  This CGI used to SELECT passCode and email the user their own password in
#  cleartext. Passwords are now bcrypt-hashed in `password_hash`, so there is
#  nothing readable left to send -- and sending one was never safe anyway.
#
#  It now issues a single-use, time-limited reset link instead:
#    * a random token is generated and emailed to the address on file
#    * only the SHA-256 of that token is stored, so a database read alone
#      cannot be replayed as a reset
#    * the token expires after one hour
#    * the same confirmation is shown whether or not the account exists, so
#      this page cannot be used to enumerate registered email addresses
#
#  The link lands on resetPassword.cgi, which sets a new password.
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
use SciMiner::Security qw(generate_token);
#use warnings;
use strict;

$CGI::LIST_CONTEXT_WARN = 0;

#  How long a reset link stays valid, in minutes.
my $RESET_TTL_MINUTES = 60;

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


#------------------------------------------------------------------------------
#  Automatically update the server's current URL for cgi-bin
#------------------------------------------------------------------------------
my $query = new CGI;
my $my_url = $query->self_url;
my @tmpSplit1 = split(/\/\//, $my_url);
my @tmpSplit2 = split(/\//, $tmpSplit1[1]);
my $tmpLocalURL = "http://$tmpSplit2[0]/";


#------------------------------------------------------------------------------
#  Initialize varialbes
#------------------------------------------------------------------------------
my $CurrentDate = `date`;


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
#	Check the transferred content
#------------------------------------------------------------------------------
if (defined param("userEmail"))
{	my $userEmail	= param("userEmail");
	$userEmail		=~ s/^\s+|\s+$//g;

	sendResetLink (\%annoENV, $userEmail);

	#  Deliberately identical whether or not the account exists: this page must
	#  not reveal which email addresses are registered.
	print "<p class=\"sectionTitleName1\" align=\"center\"><b>If a SciMiner account exists for $userEmail, a password reset link has just been sent there.</b><br><br>".
	      "The link is valid for $RESET_TTL_MINUTES minutes and can be used once.</p>";
	print_end_html();
	exit;
}else
{	# Do nothing
	print_form();
	print_end_html();
	exit;
}


#------------------------------------------------------------------------------
#	Sub-routines
#------------------------------------------------------------------------------


sub print_SciMiner_Header
{   print "<p align=\"center\" class=\"pageName\"><b><U>SciMiner Password Reset</U></b></p>
           ";
}


sub print_end_html
{   print end_html;
}


sub print_form
{	print "<p class=\"titleBarName1\"><b> Enter your email address and click submit. We will send you a link to choose a new password. </b><br>";
	print "<form name=\"form1\" action=\"lostPassword.cgi\" method=\"POST\" enctype=\"multipart/form-data\">
			Email : <INPUT TYPE='text' NAME='userEmail' size=\"35\"><br><br>
	       <input type='submit' name=\"formSubmit\" value=\"Submit\">
		   </form>
		   <br><br>";
	print "<p class=\"titleBarName1\">For your security, SciMiner can no longer email you your existing password -- passwords are stored in a form that cannot be read back. You will be asked to choose a new one.</p>";
}


sub sendResetLink
{	my $annoENVRef				= shift;
	my $userEmail				= shift;

	return (0) unless ((defined $userEmail) && ($userEmail ne ''));

	#  Database Access Information
    my $SciMinerDB  = "DBI:mysql:database=".$annoENV{DB} || return (0);
    my $username    = $annoENV{username} || return (0);
    my $password    = $annoENV{password} || return (0);

    my $dbh         = DBI->connect($SciMinerDB, $username, $password, {PrintError => 0}) || return (0);

	#  Look the account up. Placeholders here: this value comes straight from a
	#  web form and used to be interpolated into the SQL.
	my $sth			= $dbh->prepare("SELECT userID, email FROM user WHERE email = ? AND suspended = 0");
	$sth->execute($userEmail);
	my @row			= $sth->fetchrow_array;

	unless ((defined $row[0]) && ($row[0] ne ''))
	{	#  No such account. Return quietly -- the caller prints the same message
		#  either way so that this page cannot be used to enumerate addresses.
		return (0);
	}
	my $userID		= $row[0];

	#  Send to the address as STORED, never to the raw form value.
	my $sendTo		= $row[1];
	return (0) unless ((defined $sendTo) && ($sendTo =~ /\A[A-Za-z0-9._%+\-]+\@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\z/));

	#  The token goes in the email; only its SHA-256 is stored, so reading the
	#  database does not hand an attacker a usable reset link.
	my $token		= generate_token(48);
	my $tokenHash	= sha256_hex($token);

	my $upd			= $dbh->prepare("UPDATE user SET password_reset_token = ?, password_reset_expires = DATE_ADD(NOW(), INTERVAL ? MINUTE) WHERE userID = ?");
	$upd->execute($tokenHash, $RESET_TTL_MINUTES, $userID) || return (0);

	#  Build the reset URL.
	#
	#  Two things matter here. SciMinerServerURL is still recorded as http://,
	#  and the site is served over TLS -- so upgrade the scheme rather than
	#  email a link that would carry the token in the clear. And Tomcat only
	#  EXECUTES CGI under <app>/cgi-bin/ (scripts live in WEB-INF/cgi); a URL
	#  pointing straight at the .cgi file would return the Perl source instead
	#  of running it, so the path must go through cgi-bin.
	my $baseURL		= $$annoENVRef{SciMinerServerURL};
	$baseURL		=~ s{^http://}{https://};
	$baseURL		.= '/' unless ($baseURL =~ m{/\z});
	my $resetURL	= $baseURL."cgi-bin/resetPassword.cgi?token=$token";

	#  Pipe straight into mail with the LIST form of open: no shell is spawned,
	#  so the address can never be read as shell metacharacters. (The old code
	#  built a `mail ... "$userEmail" < tmpfile` backtick out of a form value.)
	my $body		= "\n\nA password reset was requested for your SciMiner account.\n\n".
					  "To choose a new password, open this link within $RESET_TTL_MINUTES minutes:\n\n".
					  "$resetURL\n\n".
					  "The link can be used once. If you did not request this, you can ignore\n".
					  "this email -- your current password remains unchanged.\n\n\n";

	my $mailFH;
	unless (open ($mailFH, '|-', 'mail', '-s', 'SciMiner -- password reset link', $sendTo))
	{	return (0);
	}
	print $mailFH $body;
	close ($mailFH);

	return (1);
}
