#!/usr/bin/perl
# Add current directory to Perl module path
use FindBin qw($RealBin);
use lib $RealBin;

#******************************************************************************
#
#                createSciMinerAccount.cgi for SciMiner on the web
#
#                                         Written By Junguk HUR
#                                         juhur @ umich . edu
#
#  Created 	: 11/16/2008
#  Desc		: This CGI allows users to create an SciMiner account
#
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
use SciMinerUI qw(print_topbar print_footer print_head_extras);
use SciMiner::Security qw(hash_password);
#use warnings;
use strict;

#here's a stylesheet incorporated directly into the page
my  $newStyle=<<END;
<!-- 
body {
    margin-left: 10px;
}
-->
END


# here is some javascript

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
print $query->start_html(-title=>'SciMiner Package Download', 
                        -author=>'InformaticsTools@gmail.com',
                        -meta=>{'keywords'	=>	'Junguk Hur SciMiner text mining text-mining bioinformatics',
                                'copyright'	=>	'copytight 2006-8 Junguk Hur'},
                        -style=>{-src=>['/SciMiner1.1/css/sciminer-modern.css'], -code=>$newStyle}
                        );
print_head_extras();
print_topbar();


#print_SciMiner_Header();



#------------------------------------------------------------------------------
#  Check parameters submitted
#------------------------------------------------------------------------------
my @errorMessage		= ();

my $userEmail			= param("userEmail");
my $userPassCode1		= param("userPassCode1");
my $userPassCode2		= param("userPassCode2");
my $userName			= param("userName");
my $userInstName		= param("userInstName");
my $userInstDeptName	= param("userInstDeptName");
my $userInstAddress		= param("userInstAddress");
my $userInstCity		= param("userInstCity");
my $userInstState		= param("userInstState");
my $userInstZipCode		= param("userInstZipCode");
my $userInstCountry		= param("userInstCountry");

my $usageAgreed			= param("usageAgreed");


#------------------------------------------------------------------------------
#	Check the transferred content
#------------------------------------------------------------------------------
if (defined param("formSubmit"))
{	
	if ((defined $usageAgreed) && ($usageAgreed eq 'I understand and accept the agreements above'))
	{	#  Check other parameters
		if ((defined $userEmail) 		&& ($userEmail ne "") 			&&
			(defined $userName) 		&& ($userName ne "") 			&&
			(defined $userPassCode1) 	&& ($userPassCode1 ne "") 		&&
			(defined $userPassCode2) 	&& ($userPassCode2 ne "") 		&&
			(defined $userInstName) 	&& ($userInstName ne "") 		&&
			(defined $userInstDeptName) && ($userInstDeptName ne "") 	&&
			(defined $userInstAddress) 	&& ($userInstAddress ne "") 	&&
			(defined $userInstCity) 	&& ($userInstCity ne "") 		&&
			(defined $userInstState) 	&& ($userInstState ne "") 		&&
			(defined $userInstZipCode) 	&& ($userInstZipCode ne "") 	&&
			(defined $userInstCountry) 	&& ($userInstCountry ne ""))
		{	
			#  Check email format
		    if ($userEmail =~ /^[\w|\.]+\@.*\..*/)
			{   # This is a profer email address
				
				if ($userPassCode1 eq $userPassCode2)
				{	#  Check pre-existing email
					if (check_preexisting_account(\%annoENV, $userEmail))
					{	push @errorMessage, "Your email is already associated with other SciMiner account. Contact the system administrator if you think this is an error.\n";
					}else
					{	
						my $insertionStatus	= save_user_info_into_database ( \%annoENV, $userEmail, $userPassCode1, $userName, $userInstName, 
															$userInstDeptName, $userInstAddress, $userInstCity, $userInstState, $userInstZipCode, $userInstCountry );
						if ($insertionStatus)
						{	print "<br><br><p class='titleBarName1' align='center'>Congratulation! Your SciMiner account has been successfully created.<br><br>Your account is limited to $annoENV{MaxDoc} (or $annoENV{MaxNewDoc} new) documents per query.<br><br>If you need to work on more documents per query, we recommend you to use the standalone versions instead.<br><br>Or contact the system administrator to request an increase. Your comments and suggestions will be greatly appreciated.<br><br><a href=\"mailto:$annoENV{AdminEmail}?subject=Regarding SciMiner\">$annoENV{AdminEmail}</a></p>";
						}
						else
						{	print "<a align='center' class='titleBarName1'>An error has occurred during account setup. <br><br>Please contact the system administrator for help.<br><br> Your comments and suggestions will be greatly appreciated.<br><br><a href=\"mailto:$annoENV{AdminEmail}?subject=Regarding SciMiner\">$annoENV{AdminEmail}</a></p>";
						}
						print_end_html();
						exit;
					}
				}else
				{	push @errorMessage, "Your passwords are not identical.\n";
				}
			}else
			{   push @errorMessage, "E-mail format is unacceptable.";
			}
		}else
		{	push @errorMessage, "Some of the required fields are not enterd.";
		}
	}else
	{	#  This means, user did not agreeded.
		push @errorMessage, "You have to accept the agreements to download the SciMiner standalone versions.";
	}
}else
{	# possible the initial screen
	print_agreement();
	print_your_information();
}




#------------------------------------------------------------------------------
#	Check error message and display
#------------------------------------------------------------------------------
if (defined $errorMessage[0])
{	display_errorMessage_SciMiner_CGI(\@errorMessage);
	print_agreement();
	print_your_information();	print_end_html();
	exit;
}else
{	# Create the URL
	print_end_html();
	exit;
}







#------------------------------------------------------------------------------
#	Sub-routines
#------------------------------------------------------------------------------


sub print_SciMiner_Header
{   print "<p align=\"center\" class=\"pageName\"><b><U>SciMiner Account Sign-up</U></b></p>
           ";
}


sub print_end_html
{   print_footer();
    print end_html;
}


sub display_errorMessage_SciMiner_CGI
{   my $errorMessageRef = shift;
    
    if (not defined $errorMessageRef)
    {   return;
    }
    
    print "<font color=\"red\">";
    for (my $i=0; $i < scalar @{$errorMessageRef}; $i++)
    {   if ($$errorMessageRef[$i] ne "")
        {   print " Error ".($i+1).": $$errorMessageRef[$i]<br>";
        }
    }
    print "</font>";
}



sub print_agreement
{	print "<br><p class=\"sectionTitleName1\" align=\"center\"><b>SciMiner Usage Agreements</b><\p>";
	print "<p class=\"titleBarName1\"><b>SciMiner is a freely available tool but the use of SciMiner is strictly limited to academic research purposes. SciMiner must not be used for any commercial purpose. We, the developers of the SciMiner, and the University of North Dakota are not responsible in away for any trouble that might be caused by use or alteration of the SciMiner system. It must be noted that the copyrights of the processed articles belong to their respective publishers not to the SciMiner users or developers.</b></p>";
	print "<form name=\"form1\" action=\"createSciMinerAccount.cgi\" method=\"POST\" enctype=\"multipart/form-data\">
			<u>Check here if you understand and accept the agreements above.</u>
			<input type=\"checkbox\" name=\"usageAgreed\" value=\"I understand and accept the agreements above\"><br><br>";
}


			

sub print_your_information
{	print "<p class=\"sectionTitleName1\" align=\"center\"><b>Your Information</b><\p>";
	print "<p class=\"titleBarName1\">Fill out the following contact information and click 'Submit' button. Please, use your <b>institutional</b> information here and <b>all fields are required</b>.</p>
	
			<table border='1' class=\"titleBarName1\">
				<tr>
					<th width='200'>
						Institutional Email
					</th>
					<td width='300'>
						<INPUT TYPE='text' NAME='userEmail' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Password (~20 charcters)
					</th>
					<th>
						<INPUT TYPE='password' NAME='userPassCode1' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Password (Repeat here)
					</th>
					<th>
						<INPUT TYPE='password' NAME='userPassCode2' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Your Full Name
					</th>
					<th>
						<INPUT TYPE='text' NAME='userName' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Institution
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstName' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Department 
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstDeptName' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Address
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstAddress' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						City
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstCity' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						State
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstState' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Zip code
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstZipCode' size=\"35\">
					</td>				
				</tr>
				<tr>
					<th>
						Country
					</th>
					<th>
						<INPUT TYPE='text' NAME='userInstCountry' size=\"35\">
					</td>				
				</tr>
			</table>
			
		<br>
		 <input type='submit' name=\"formSubmit\" value=\"Submit\">&nbsp;&nbsp;<INPUT TYPE=\"RESET\">

	</form>
	<br><br>
			  ";
			
}




sub check_preexisting_account
{	my $annoENVRef				= shift;
	my $email					= shift;

	#  Database Access Information
    my $SciMinerDB  = "DBI:mysql:database=".$annoENV{DB} || return (-1, "!ERROR: No database specified");
    my $username    = $annoENV{username} || return (-1, "!ERROR: No username specified");
    my $password    = $annoENV{password} || return (-1, "!ERROR: No password specified");


    #  ------------------------------------------------------------------------
    #  Retrieve User Information from SciMinerDB
    #  ------------------------------------------------------------------------
    my $dbh         = DBI->connect($SciMinerDB, $username, $password, {PrintError => 0}) || 
                      return (-1, "!ERROR: Couldn't connect to database ".$DBI::errstr);

	#  Retrieve the downloadHistoryID
	my $sth			= $dbh->prepare("SELECT userID FROM user WHERE email like '$email'");
    $sth->execute();
    my @row         = $sth->fetchrow_array;#($result);
	if ((defined  $row[0]) && ($row[0] ne ""))
	{	return(1);
	}else
	{	return(0);
	}
}








sub save_user_info_into_database
{	my $annoENVRef				= shift;
	my $email					= shift;
	my $userPassCode1			= shift;
	my $name					= shift;
	my $instName				= shift;
	my $instDeptName			= shift;
	my $instAddress				= shift;
	my $instCity				= shift;
	my $instState 				= shift;
	my $instZipCode				= shift;
	my $instCountry		 		= shift;
													
	my $insertionStatus			= 1;
	
	#  Database Access Information
    my $SciMinerDB  = "DBI:mysql:database=".$annoENV{DB} || return (-1, "!ERROR: No database specified");
    my $username    = $annoENV{username} || return (-1, "!ERROR: No username specified");
    my $password    = $annoENV{password} || return (-1, "!ERROR: No password specified");


    #  ------------------------------------------------------------------------
    #  Retrieve User Information from SciMinerDB
    #  ------------------------------------------------------------------------
    my $dbh         = DBI->connect($SciMinerDB, $username, $password, {PrintError => 0}) || 
                      return (-1, "!ERROR: Couldn't connect to database ".$DBI::errstr);

	my $columns		= 'email, name, passCode, password_hash, maxDoc, maxNewDoc, editLevel, institute, deptOrLab, instAddress, instCity, instState, instZipCode, instCountry, signUpDate, signUpTime, activationCode';

	#  ------------------------------------------------------------------------
	#  Signup no longer stores the password in cleartext.
	#
	#  `passCode` is written EMPTY on purpose. SciMiner_email_password_check
	#  guards its cleartext fallback with ($passCode ne ''), so an empty column
	#  means this account authenticates against the bcrypt hash only -- there is
	#  no cleartext path for any account created from here on.
	#
	#  Fail CLOSED: if hashing fails, abort the signup rather than silently
	#  falling back to storing the password in the clear.
	#  ------------------------------------------------------------------------
	my $passwordHash	= eval { hash_password($userPassCode1) };
	if ((! defined $passwordHash) || ($passwordHash eq ''))
	{	print "!ERROR: Could not secure the password. The account was NOT created. Please contact $$annoENVRef{AdminEmail}.";
		return(0);
	}

	#  ------------------------------------------------------------------------
	#  2026-08-13: `activationCode` is declared NOT NULL with no DEFAULT, and
	#  this INSERT never supplied it. Under STRICT_TRANS_TABLES (which this
	#  server runs) MySQL rejects the whole statement with
	#      Field 'activationCode' doesn't have a default value
	#  so signup through SciMiner 1.1 has been failing for every user. Supply a
	#  value. `activationStatus` (DEFAULT 1 = active) and `suspended`
	#  (DEFAULT 0) are deliberately left to their schema defaults: 1.1 has no
	#  activateAccount.cgi, and its success page tells the user the account is
	#  ready to use, so an inactive account here would strand them.
	#  ------------------------------------------------------------------------
	my $tmpCode			= '';
	my @chars			= ('a'..'z','A'..'Z','0'..'9','_');
	foreach (1..50)
	{	$tmpCode		.= $chars[rand @chars];
	}

	#  Remove any ' or "
	$name				=~ s/\"|\'//g;
	$instName			=~ s/\"|\'//g;
	$instDeptName		=~ s/\"|\'//g;
	$instAddress		=~ s/\"|\'//g;
	$instCity			=~ s/\"|\'//g;
	$instState			=~ s/\"|\'//g;
	$instZipCode		=~ s/\"|\'//g;
	$instCountry		=~ s/\"|\'//g;
	
	
	#  Try to insert content
    $dbh->do("INSERT INTO `user` ($columns) VALUES (\"$email\", \"$name\", \"\", \"$passwordHash\", $$annoENVRef{MaxDoc}, $$annoENVRef{MaxNewDoc}, 3, \"$instName\", \"$instDeptName\", \"$instAddress\", \"$instCity\", \"$instState\", \"$instZipCode\", \"$instCountry\", curdate(), curtime(), \"$tmpCode\")");
    
    if ((defined $DBI::errstr) && ($DBI::errstr ne ""))
    {	$insertionStatus	= 0;
    	print $DBI::errstr;
    	return($insertionStatus);
    }
    
    #  Retrieve the userID
	my $sth			= $dbh->prepare("SELECT userID FROM user ORDER BY userID DESC LIMIT 1");
    $sth->execute();
    my @row         = $sth->fetchrow_array;#($result);
    my $userID	= $row[0];
    
	#  Send an information email to the system administrator	
	my $fileName		= int(rand(1000000000000000000)).'.txt';
	my $resultFile		= "/tmp/$fileName";
	open (TMP, ">".$resultFile);
	print TMP 	"\nDear System Administrator,\n\n".
			 	"Here is the detail of a new user.\n\n".
			 	"userID	:	$userID\n".
			 	"email	:	$email\n".
			 	"passCode	:	********\n".
			 	"name	:	$name\n".
			 	"maxDoc	:	$$annoENVRef{maxDoc}\n".
			 	"maxNewDoc	:	$$annoENVRef{maxNewDoc}\n".
			 	"editLevel	:	3\n".
			 	"instName	:	$instName\n".
			 	"instDeptName	:	$instDeptName\n".
			 	"instAddress	:	$instAddress\n".
			 	"instCity	:	$instCity\n".
			 	"instState	:	$instState\n".
			 	"instZipCode	:	$instZipCode\n".
			 	"instCountry	:	$instCountry\n\n\n".
			 	"!!! DO NOT REPLY TO THIS EMAIL !!!\n".
			 	"! If you have any question, email to the system administrator $$annoENVRef{AdminEmail}\n\n";
	close TMP;
	
	`mail -s \"SciMiner -- A new user account has been created.\" \"$$annoENVRef{AdminEmail}\" < $resultFile`;
    unlink ($resultFile);

	return($insertionStatus);
}






