#############################################################################
#       
#               Subroutin Collection for basic IO for "SciMinerDB"
#
#                                                   By: Junguk Hur
#                                                       juhur <at> umich.edu
#
#   Last modified: 09/13/2007
#
#############################################################################
use strict;
use warnings;



# ----------------------------------------------------------------------------
# Global Variable
# ----------------------------------------------------------------------------
my @annoINIPath;  # Will be dynamically initialized





# ---------------------------------------------------------------------------
# sub anno_environmental_file_open
# ---------------------------------------------------------------------------
# anno_environmental_file_open
# A subroutine to load the annotation environment file and load it into the MEM.
sub anno_environmental_file_open
{   my $annoFileLoaded = 'no';
    my %annoENV;

    # Initialize dynamic paths if not already done
    if (!@annoINIPath) {
        # Try to determine base directory
        my $base_dir = $ENV{SCIMINER_HOME} || '/home/hurlab/apache-tomcat-9.0.37/webapps/SciMiner1.1';

        #  2026-08-13: annotationENV.ini holds the MySQL username and password.
        #  It used to live under webapps/SciMiner1.1/annotation/SciMinerDB/,
        #  which Tomcat serves as STATIC FILES -- so the live credential was
        #  downloadable at
        #    /SciMiner1.1/annotation/SciMinerDB/annotationENV.ini
        #  by anyone, with no authentication (verified 200 from off-host).
        #  File permissions cannot fix this: Tomcat runs as the same user that
        #  owns the file. The config therefore lives OUTSIDE the served tree
        #  and that location is searched FIRST. This mirrors the SciMiner 2.0
        #  fix, where .env was relocated to /etc/sciminer2/.
        #  The in-webapps paths are kept as trailing fallbacks so that a tree
        #  without the relocated file still starts.
        @annoINIPath = ( "/home/hurlab/ANNOTATION-SciMiner1.1/SciMinerDB/",
                         "$base_dir/annotation/SciMinerDB/",
                         "/home/hurlab/apache-tomcat-9.0.37/webapps/SciMiner1.1/annotation/SciMinerDB/",
                         "$base_dir/ANNOTATION/SciMinerDB/");
    }

    foreach (@annoINIPath)
    {   unless(open(ANNO_ENV , $_.'annotationENV.ini'))
        {   next;
        }
        my @filedata = <ANNO_ENV>;
        foreach my $line (@filedata) 
        {   $line =~ s/\r|\n//g;
            my @localTemp= split( /\=/ ,$line);
	    if (not defined $localTemp[0])
		{	next;
		}
            $annoENV{$localTemp[0]}=$localTemp[1];                
        }   close ANNO_ENV;   
        $annoFileLoaded = 'yes';
        last;
    }

    if ($annoFileLoaded eq 'no')
    {   die "\nCannot open Annotation Environment File \n\n\t\"annotationENV.ini\" \n\nPlease check it again.\n\n";
    }else
    {   return %annoENV;
    }
}








# ---------------------------------------------------------------------------
# sub Gene_Ontology_Code_Creation
# ---------------------------------------------------------------------------
# Last modified 10/2/2006
# sub Gene_Ontology_Code_Creation
# date: 10/2/2006
# This subroutin create a code for gene ontology
sub Gene_Ontology_Code_Creation
{   my ($GOFile, $code, $max, $maxCode, $fileHandle) = @_;
    open ( FILE, $GOFile);
    while (<FILE>)
    {   my $a = $_;   $a =~ s/\r|\n//g;
        my $space_start = 0;
        my $first_letter = substr($a,0,1);
        my $count=0;                
        my $relation='1';           my @c = ();
        my $num=0;                  my $goid = '';
        my @e = ();                 my $def = '';
        
        if (( $first_letter ne '!' ) && ( $first_letter ne'$' ))
        {   while ($first_letter eq ' ')
            {   substr($a,0,1)='';        # remove one space
                $first_letter=substr($a,0,1);
                $count++;
            }
    
            @c = split(/\s/, $code);
            $num = $count;
            $c[$count-1]++;
    
            # Fill zero for remaining positions
            while ($num < 20)
            {   $c[$num] = 0;
                $num++;
            }
    
            # Merge tmp code        
            $code = join (' ', @c);
            if ( $max < $count )
            {   $max = $count;
                $maxCode = $code;
            }
    
            substr($a, 0, 1) = '';  #remove the special character
            @e = split(/\;/, $a);
            substr($e[0], -1, 1) = '';
            $def = $e[0];
            $goid = substr($e[1], 1, 10);
            print $fileHandle "$code\t$def\t$goid\t\n";
        } #if ( $first_letter ne '!'
    }   close FILE;
    return ($maxCode, $max);
}




sub LogQuery
{   my $message 	= shift;
	open (OUT, ">>".'/tmp/SciMinerQuery.log');
    print OUT get_current_time_full(), "  \t".$message."\n";
    close OUT;
}


sub LogGRIFQuery
{   my $message 	= shift;
	open (OUT, ">>".'/tmp/SciMinerGRIFQuery.log');
    print OUT get_current_time_full(), "  \t".$message."\n";
    close OUT;
}


sub SciMinerLog_SA
{   my $message = shift;
	print get_current_time_full(), "  \t".$message."\n";
}


sub LogAnalysis
{   my $message 	= shift;
	open (OUT, ">>".'/tmp/SciMinerAnalysis.log');
    print OUT get_current_time_full(), "  \t".$message."\n";
    close OUT;
}




sub get_current_time_short
{   #my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
    #my @weekDays = qw(Sun Mon Tue Wed Thu Fri Sat Sun);
    my ($second, $minute, $hour, $dayOfMonth, $month, $yearOffset, $dayOfWeek, $dayOfYear, $daylightSavings) = localtime();
    # $year = 1900 + $yearOffset;
    my $theTime = "$hour:$minute:$second"; #, $weekDays[$dayOfWeek] $months[$month] $dayOfMonth, $year";
    return ($theTime);
}





sub get_current_time_full
{   my @months = qw(Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec);
    my @weekDays = qw(Sun Mon Tue Wed Thu Fri Sat Sun);
    my ($second, $minute, $hour, $dayOfMonth, $month, $yearOffset, $dayOfWeek, $dayOfYear, $daylightSavings) = localtime();
    my $year = 1900 + $yearOffset;
    my $theTime = "$months[$month] $dayOfMonth ($weekDays[$dayOfWeek])\t$hour:$minute:$second";
    return ($theTime);
}





sub short_name_ext
{   my ($fileArray, $extension) = @_;
    my @localShortArray = ();
    if (not defined $extension)
    {   $extension = '\.';
    }

    foreach (@{$fileArray})
    {   my @tmp1 = split (/\//, $_);
        my @tmp2 = split (/$extension/, $tmp1[$#tmp1]);
        push @localShortArray, $tmp2[0];
    }
    return (@localShortArray);
}







# shortFileNameExtraction
# Last modified: 12/08/06
# A subroutine to make short file name for directory creation
sub shortFileNameExtraction 
{   my ( $fullFileName ) = @_;
    my @shortFileName = ();
    my $totalFileNumber = scalar ( @$fullFileName );

    use strict;
    use warnings;

    for ( my $i=0;  $i < $totalFileNumber ; $i++ )
    {   my @temp  = split(/\//, @$fullFileName[$i] );
        $shortFileName[$i] = $temp[$#temp];
    }
    return @shortFileName;
}






# shortFileNameExtractionWOExt
# Last modified: 12/08/06
# A subroutine to make extract short file names without extension
sub shortFileNameExtractionWOExt 
{   my ($fullFileName) = @_;
    my @shortFileName = ();
    my $totalFileNumber = scalar ( @$fullFileName );

    use strict;
    use warnings;

    for ( my $i=0;  $i < $totalFileNumber ; $i++ )
    {   my @temp  = split(/\//, @$fullFileName[$i]);
        my @temp2 = split(/\./, $temp[$#temp]);
        my @temp3 = split(/\.$temp2[$#temp2]/, $temp[$#temp]);
        $shortFileName[$i] = $temp3[0];
    }
    return @shortFileName;
}




# July 3, 2004
# shortFileNameExtraction {
# A subroutine to make short file name for directory creation
sub fileExtensionRemovalForSingleFile 
{   my ($fullFileName) = @_;
    my @tempSplit = split ( /\./, $fullFileName );
    my $extensionLength = length ( $tempSplit[$#tempSplit] );
    for (my $i=0; $i <= $extensionLength; $i++ )
    {   substr ($fullFileName, -1,1 ) = '';
    }   return $fullFileName;
}

###########################################################################################
1;
