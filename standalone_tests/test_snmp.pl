#!/usr/bin/env perl -w

use strict;
use Net::SNMP;
use Time::HiRes qw ( usleep gettimeofday );
use POSIX;

my ($host, $comm, $port, $oid_sig) = ('192.168.1.26', 'public', 161, 
	'.1.3.6.1.4.1.14988.1.1.1.1.1.4.5');

local *FOUT;
my ($it, $session, $error, $begin, $end, $osig, $nsig, 
	$ossig, $nssig, $fname, $nvals, $sout) = 
	(0, undef, 'No error', 0, 0, 0, 0, 0, 0, '', 0, 0);
my @sigv = ();

($session, $error) = Net::SNMP->session(
	-hostname => $host, -community => $comm, -port => $port);

until (defined($session)) {
	printf("ERROR: %s.\n", $error);
	die; };

if (($fname = shift @ARGV) && open(FOUT, "> $fname")) {
	close(FOUT);
	unlink($fname);
} else {
	$sout = 1;
	*FOUT = *STDOUT;
};

(($nvals = shift @ARGV) && ($nvals =~ m!^\d+!) && ($nvals = $nvals + 0) &&
	($nvals % 2)) || ($nvals = 21);

sub do_shutdown ($) {
	defined($session) && $session->close;
	$end = gettimeofday;
	my $time = $end - $begin;
	if (!$time) { printf("FATAL: 0 sec elapsed\n"); }
	elsif (!$it) { printf("FATAL: 0 iters finished\n"); }
	else { printf("%d iters takes %.3f seconds => %.2f iter/sec, %.5f sec/iter\n",
		$it, $time, $it/$time, $time/$it) };
	fileno(FOUT) && close(FOUT);
	exit $_[$[];
};

sub got_int {
	printf("\nINTERRUPT. Exiting after %d iterations\n", $it);
	do_shutdown(1);
};

$SIG{INT} = \&got_int; 

sub get_sig {
	my ($result, $sig_val);
	$result = $session->get_request(-varbindlist => [$oid_sig]);

	unless (defined($result)) {
		printf("ERROR: %s.\n", $session->error);
		#do_shutdown(1);
		return;
	};

	unless ($sig_val = $result->{$oid_sig} + 0) {
		printf('ERROR: non-numeric value "%s" for OID "%s"\n',
			$result->{$oid_sig}, $oid_sig);
		do_shutdown(1);
	};

	return $sig_val;
};

sub write_val ($) {
	#!$sout && -e $fname && return;
	#seek(FOUT, 0, 0);
	$sout || open(FOUT, "> $fname") || return;
	print(FOUT $_[$[], "\n");
	#truncate(FOUT, tell(FOUT));
	close(FOUT) unless $sout;
};

sub mean {
	my ($sum, $val) = (0, 0);
	foreach $val (@_) {$sum += $val};
	return ($sum/@_);
};

sub median {
	my @sigs = sort { $a <=> $b } @_;
	return ($sigs[$[ + @sigs/2]);
};

sub qmean {
	my @sigs = sort { $a <=> $b } @_;
	my $q = ceil(floor(@sigs/2)/2);
	splice (@sigs, $[, $q);
	# Dont use splice(@sigs, -$q)!
	@sigs = reverse(@sigs);
	splice (@sigs, $[, $q);
	return (mean(@sigs));
};

sub cls {
	print("\033[2J");
	print("\033[0;0H");
};


$osig = get_sig();
write_val($osig);

$begin = gettimeofday;

#for ($it = 0; $it < 1000; $it++) {
$it = 0;
while (1) {
	($nsig = get_sig()) || next;

	cls();
	printf("Signal level for host '%s' is %d\n", 
		$session->hostname, $nsig);

	# Do not need for now!
	next;
	#usleep(5000);

	if (1 || ($nsig != $osig)) {
		push @sigv, $nsig;
		if (@sigv >= $nvals) {
			$nssig = median(@sigv);
			if ($nssig != $ossig) {
				printf("Signal level changed: %d (%s)\n", 
					$nssig, join(", ", @sigv));
				#write_val($nssig);
			};
			$ossig = $nssig;
			shift @sigv;
			#@sigv = ();
		};
	};

	$osig = $nsig;

	$it++;
};

do_shutdown(0);
