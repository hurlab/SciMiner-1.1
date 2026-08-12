package SciMiner::Security;
use strict;
use warnings;
use Crypt::Eksblowfish::Bcrypt qw(bcrypt en_base64);
use MIME::Base64 qw(encode_base64);
use Exporter qw(import);
our @EXPORT_OK = qw(hash_password verify_password generate_token);

# Hash a password using bcrypt
sub hash_password {
    my ($password) = @_;
    die "Password required" unless defined $password;

    # Generate a 16-byte random salt, encoded with bcrypt's base64 variant.
    #
    # Do NOT hand-roll this as "pick 22 random characters": a bcrypt salt encodes
    # 128 bits in 22 base64 characters, so the final character carries only 2
    # significant bits and just 4 of the 64 characters are legal there. Choosing
    # it uniformly made bcrypt() die with "bad base64 encoding" ~94% of the time
    # (measured: 2 successes in 50 calls). en_base64() always emits a valid salt.
    my $raw = '';
    if (open my $urandom, '<:raw', '/dev/urandom') {
        read $urandom, $raw, 16;
        close $urandom;
    }
    if (length($raw) != 16) {
        # Fallback only if /dev/urandom is unavailable.
        $raw = join '', map { chr int rand 256 } (1..16);
    }
    my $salt = en_base64($raw);

    # Cost factor (higher = more secure but slower)
    my $cost = 12;

    # Create the bcrypt hash
    my $hash = bcrypt($password, '$2a$' . $cost . '$' . $salt);

    return $hash;
}

# Verify a password against its hash
sub verify_password {
    my ($password, $stored_hash) = @_;
    return 0 unless defined $password && defined $stored_hash;

    # Extract the salt from the stored hash
    return bcrypt($password, $stored_hash) eq $stored_hash;
}

# Generate a random token for sessions, CSRF, etc.
sub generate_token {
    my $length = shift || 32;
    my @chars = ('a'..'z', 'A'..'Z', 0..9);
    my $token = join '', map $chars[rand @chars], 1..$length;
    return $token;
}

1;