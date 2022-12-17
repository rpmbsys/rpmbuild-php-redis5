# Fedora spec file for php-pecl-redis5
# without SCL compatibility from:
#
# remirepo spec file for php-pecl-redis5
#
# Copyright (c) 2012-2022 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#

# we don't want -z defs linker flag
%undefine _strict_symbol_defs_build

%define _debugsource_template %{nil}
%define debug_package %{nil}

%global pecl_name   redis
%global with_zts    0%{!?_without_zts:%{?__ztsphp:1}}
%ifarch s390x ppc64le
%bcond_with         tests
%else
%if 0%{?fedora} >= 33 || 0%{?rhel} >= 9
%bcond_without      tests
%else
%bcond_with         tests
%endif
%endif
%bcond_without      lzf

# after 20-json, 40-igbinary and 40-msgpack
%global ini_name    50-%{pecl_name}.ini
%global upstream_version 5.3.7
#global upstream_prever  RC2

Summary:       Extension for communicating with the Redis key-value store
Name:          php-pecl-redis5
Version:       %{upstream_version}%{?upstream_prever:~%{upstream_prever}}
Release:       1%{?dist}
Source0:       https://pecl.php.net/get/%{pecl_name}-%{upstream_version}%{?upstream_prever}.tgz
License:       PHP
URL:           https://pecl.php.net/package/redis

BuildRequires: make
BuildRequires: gcc
BuildRequires: php-devel >= 7.0
BuildRequires: php-pear
BuildRequires: php-json
BuildRequires: php-pecl-igbinary-devel
BuildRequires: php-pecl-msgpack-devel >= 2.0.3
%if %{with lzf}
BuildRequires: pkgconfig(liblzf)
%else
Provides:      bundled(liblzf) = 3.6
%endif
BuildRequires: pkgconfig(libzstd) >= 1.3.0
BuildRequires: pkgconfig(liblz4)
# to run Test suite
%if %{with tests}
BuildRequires: redis >= 6
%endif

Requires:      php(zend-abi) = %{php_zend_api}
Requires:      php(api) = %{php_core_api}
Requires:      php-json%{?_isa}
Requires:      php-pecl(igbinary)%{?_isa}
Requires:      php-pecl-msgpack%{?_isa}

Obsoletes:     php-%{pecl_name}               < 3
Provides:      php-%{pecl_name}               = %{version}
Provides:      php-%{pecl_name}%{?_isa}       = %{version}
Provides:      php-pecl(%{pecl_name})         = %{version}
Provides:      php-pecl(%{pecl_name})%{?_isa} = %{version}

%if 0%{?fedora} >= 31 || 0%{?rhel} >= 8
Obsoletes:     php-pecl-%{pecl_name}          < 5
Provides:      php-pecl-%{pecl_name}          = %{version}-%{release}
Provides:      php-pecl-%{pecl_name}%{?_isa}  = %{version}-%{release}
Obsoletes:     php-pecl-%{pecl_name}4         < 5
Provides:      php-pecl-%{pecl_name}4         = %{version}-%{release}
Provides:      php-pecl-%{pecl_name}4%{?_isa} = %{version}-%{release}
%else
# A single version can be installed
Conflicts:     php-pecl-%{pecl_name}  < 5
Conflicts:     php-pecl-%{pecl_name}4 < 5
%endif


%description
The phpredis extension provides an API for communicating
with the Redis key-value store.

This Redis client implements most of the latest Redis API.
As method only only works when also implemented on the server side,
some doesn't work with an old redis server version.


%prep
%setup -q -c
# rename source folder
mv %{pecl_name}-%{upstream_version}%{?upstream_prever} NTS

# Don't install/register tests, license, and bundled library
sed -e 's/role="test"/role="src"/' \
    -e '/COPYING/s/role="doc"/role="src"/' \
%if %{with lzf}
    -e '/liblzf/d' \
%endif
    -i package.xml

cd NTS
# Use system library
%if %{with lzf}
rm -r liblzf
%endif

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_REDIS_VERSION/{s/.* "//;s/".*$//;p}' php_redis.h)
if test "x${extver}" != "x%{upstream_version}%{?upstream_prever}"; then
   : Error: Upstream extension version is ${extver}, expecting %{upstream_version}%{?upstream_prever}.
   exit 1
fi
cd ..

%if %{with_zts}
# duplicate for ZTS build
cp -pr NTS ZTS
%endif

# Drop in the bit of configuration
cat > %{ini_name} << 'EOF'
; Enable %{pecl_name} extension module
extension = %{pecl_name}.so

; phpredis can be used to store PHP sessions.
; To do this, uncomment and configure below

; RPM note : save_handler and save_path are defined
; for mod_php, in /etc/httpd/conf.d/php.conf
; for php-fpm, in %{_sysconfdir}/php-fpm.d/*conf

;session.save_handler = %{pecl_name}
;session.save_path = "tcp://host1:6379?weight=1, tcp://host2:6379?weight=2&timeout=2.5, tcp://host3:6379?weight=2"

; Configuration
;redis.arrays.algorithm = ''
;redis.arrays.auth = ''
;redis.arrays.autorehash = 0
;redis.arrays.connecttimeout = 0
;redis.arrays.consistent = 0
;redis.arrays.distributor = ''
;redis.arrays.functions = ''
;redis.arrays.hosts = ''
;redis.arrays.index = 0
;redis.arrays.lazyconnect = 0
;redis.arrays.names = ''
;redis.arrays.pconnect = 0
;redis.arrays.previous = ''
;redis.arrays.readtimeout = 0
;redis.arrays.retryinterval = 0
;redis.clusters.auth = 0
;redis.clusters.cache_slots = 0
;redis.clusters.persistent = 0
;redis.clusters.read_timeout = 0
;redis.clusters.seeds = ''
;redis.clusters.timeout = 0
;redis.pconnect.pooling_enabled = 1
;redis.pconnect.connection_limit = 0
;redis.pconnect.echo_check_liveness = 1
;redis.pconnect.pool_pattern => ''
;redis.session.lock_expire = 0
;redis.session.lock_retries = 10
;redis.session.lock_wait_time = 2000
;redis.session.locking_enabled = 0
EOF


%build
%{?dtsenable}

peclconf() {
%configure \
    --enable-redis \
    --enable-redis-session \
    --enable-redis-igbinary \
    --enable-redis-msgpack \
    --enable-redis-lzf \
%if %{with lzf}
    --with-liblzf \
%endif
    --enable-redis-zstd \
    --with-libzstd \
    --enable-redis-lz4 \
    --with-liblz4 \
    --with-php-config=$1
}

cd NTS
%{_bindir}/phpize
peclconf %{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
peclconf %{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
%{?dtsenable}

# Install the NTS stuff
make -C NTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

%if %{with_zts}
# Install the ZTS stuff
make -C ZTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Install the package XML file
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

# Documentation
cd NTS
for i in $(grep 'role="doc"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


%check
# simple module load test
DEPS="--no-php-ini"
%if "%{php_version}" < "8.0"
DEPS="$DEPS --define extension=json.so"
%endif
DEPS="$DEPS --define extension=igbinary.so"
DEPS="$DEPS --define extension=msgpack.so"

%{__php} $DEPS \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep '^%{pecl_name}$'

%if %{with_zts}
%{__ztsphp} $DEPS \
    --define extension=%{buildroot}%{php_ztsextdir}/%{pecl_name}.so \
    --modules | grep '^%{pecl_name}$'
%endif

%if %{with tests}
cd NTS/tests

: Launch redis server
mkdir -p data
pidfile=$PWD/redis.pid
port=$(%{__php} -r 'echo 9000 + PHP_MAJOR_VERSION*100 + PHP_MINOR_VERSION*10 + PHP_INT_SIZE;')
%{_bindir}/redis-server   \
    --bind      127.0.0.1      \
    --port      $port          \
    --daemonize yes            \
    --logfile   $PWD/redis.log \
    --dir       $PWD/data      \
    --pidfile   $pidfile


: Run the test Suite
sed -e "s/6379/$port/" -i *.php

ret=0
export TEST_PHP_EXECUTABLE=%{__php}
export TEST_PHP_ARGS="$DEPS \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so"
$TEST_PHP_EXECUTABLE $TEST_PHP_ARGS TestRedis.php || ret=1

: Cleanup
if [ -f $pidfile ]; then
   %{_bindir}/redis-cli -p $port shutdown
fi
cat $PWD/redis.log

exit $ret
%else
: Upstream test suite disabled
%endif


%files
%license NTS/COPYING
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{name}.xml

%{php_extdir}/%{pecl_name}.so
%config(noreplace) %{php_inidir}/%{ini_name}

%if %{with_zts}
%{php_ztsextdir}/%{pecl_name}.so
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%endif


%changelog
* Wed Feb 16 2022 Remi Collet <remi@remirepo.net> - 5.3.7-1
- update to 5.3.7

* Thu Mar 25 2021 Remi Collet <remi@remirepo.net> - 5.3.4-1
- update to 5.3.4
- add patch for 32-bit build from
  https://github.com/phpredis/phpredis/pull/1957

* Thu Oct 22 2020 Remi Collet <remi@remirepo.net> - 5.3.2-1
- update to 5.3.2

* Wed Jul  8 2020 Remi Collet <remi@remirepo.net> - 5.3.1-1
- update to 5.3.1

* Wed Jul  1 2020 Remi Collet <remi@remirepo.net> - 5.3.0-1
- update to 5.3.0
- enable lz4 compression support
- add new option in provided configuration file

* Wed May  6 2020 Remi Collet <remi@remirepo.net> - 5.2.2-1
- update to 5.2.2
- refresh options in provided configuration file

* Mon Nov 12 2019 Remi Collet <remi@remirepo.net> - 5.1.1-1
- update to 5.1.1

* Mon Nov  4 2019 Remi Collet <remi@remirepo.net> - 5.1.0-1
- update to 5.1.0
- enable ZSTD compression support

* Tue Jul 30 2019 Remi Collet <remi@remirepo.net> - 5.0.2-1
- update to 5.0.2

* Fri Jul 12 2019 Remi Collet <remi@remirepo.net> - 5.0.1-1
- update to 5.0.1

* Tue Jul  2 2019 Remi Collet <remi@remirepo.net> - 5.0.0-1
- update to 5.0.0

* Wed Jun 26 2019 Remi Collet <remi@remirepo.net> - 5.0.0~RC2-1
- update to 5.0.0RC2

* Thu Jun 20 2019 Remi Collet <remi@remirepo.net> - 5.0.0~RC1-1
- update to 5.0.0RC1
- rename to php-pecl-redis5
- raise dependency on PHP 7
- enable msgpack support
- enable json support
- update configuration for new options
- open https://github.com/phpredis/phpredis/pull/1578
  fix extension dependencies and report about json serializer

* Wed May 29 2019 Remi Collet <remi@remirepo.net> - 4.3.0-3
- rebuild

* Wed May 22 2019 Remi Collet <remi@remirepo.net> - 4.3.0-2
- cleanup

* Thu Mar 14 2019 Remi Collet <remi@remirepo.net> - 4.3.0-1
- update to 4.3.0 (stable)

* Wed Mar  6 2019 Remi Collet <remi@remirepo.net> - 4.3.0~RC2-1
- update to 4.3.0RC2 (beta)

* Mon Feb 25 2019 Remi Collet <remi@remirepo.net> - 4.3.0~RC1-1
- update to 4.3.0RC1 (alpha)
  no change sincy 4.2.1RC1, only version change according to semver
  see https://github.com/phpredis/phpredis/issues/1517

* Mon Feb 25 2019 Remi Collet <remi@remirepo.net> - 4.2.1~RC1-1
- update to 4.2.1RC1 (alpha)
- update provided configuration with new runtime option

* Tue Dec 11 2018 Remi Collet <remi@remirepo.net> - 4.2.0-3
- test build for upstream patch

* Tue Dec  4 2018 Remi Collet <remi@remirepo.net> - 4.2.0-2
- open https://github.com/phpredis/phpredis/issues/1472
  tests failing with redis 5.0.2

* Sun Nov 18 2018 Remi Collet <remi@remirepo.net> - 4.2.0-1
- update to 4.2.0 (stable)

* Fri Nov  9 2018 Remi Collet <remi@remirepo.net> - 4.2.0~RC3-1
- update to 4.2.0RC3 (beta)

* Wed Nov  7 2018 Remi Collet <remi@remirepo.net> - 4.2.0~RC2-2
- test build for https://github.com/phpredis/phpredis/pull/1444

* Fri Oct 26 2018 Remi Collet <remi@remirepo.net> - 4.2.0~RC2-1
- update to 4.2.0RC2 (beta)
- open https://github.com/phpredis/phpredis/issues/1437 32-bit failed test

* Sun Oct 21 2018 Remi Collet <remi@remirepo.net> - 4.2.0~RC1-2
- test build with upstream patches

* Fri Oct 12 2018 Remi Collet <remi@remirepo.net> - 4.2.0~RC1-1
- update to 4.2.0RC1 (alpha)

* Thu Aug 16 2018 Remi Collet <remi@remirepo.net> - 4.1.1-2
- rebuild for 7.3.0beta2 new ABI

* Sun Aug  5 2018 Remi Collet <remi@remirepo.net> - 4.1.1-1
- update to 4.1.1

* Tue Jul 17 2018 Remi Collet <remi@remirepo.net> - 4.1.0-2
- rebuld for 7.3.0alpha4 new ABI

* Tue Jul 10 2018 Remi Collet <remi@remirepo.net> - 4.1.0-1
- update to 4.1.0 (stable)

* Fri Jun 22 2018 Remi Collet <remi@remirepo.net> - 4.1.0~RC3-1
- update to 4.1.0RC3 (beta, no change)
- drop patches merged upstream

* Fri Jun  8 2018 Remi Collet <remi@remirepo.net> - 4.1.0~RC1-2
- test build with 7.3
- open https://github.com/phpredis/phpredis/pull/1366
  Fix: Warning: time() expects exactly 0 parameters, 1 given ...

* Fri Jun  8 2018 Remi Collet <remi@remirepo.net> - 4.1.0~RC1-1
- update to 4.1.0RC1 (alpha)
- open https://github.com/phpredis/phpredis/pull/1365
  use PHP_BINARY instead of php and allow override
- report https://github.com/phpredis/phpredis/issues/1364
  missing files in pecl archive
- add new redis.session.lock* options in provided configuration

* Wed Apr 25 2018 Remi Collet <remi@remirepo.net> - 4.0.2-1
- update to 4.0.2

* Wed Apr 18 2018 Remi Collet <remi@remirepo.net> - 4.0.1-1
- update to 4.0.1

* Mon Mar 19 2018 Remi Collet <remi@remirepo.net> - 4.0.0-1
- update to 4.0.0 (stable)

* Sat Mar  3 2018 Remi Collet <remi@remirepo.net> - 4.0.0~RC2-1
- update to 4.0.0RC2

* Wed Feb  7 2018 Remi Collet <remi@remirepo.net> - 4.0.0~RC1-4
- re-enable s390x build (was a temporary failure)

* Wed Feb  7 2018 Remi Collet <remi@remirepo.net> - 4.0.0~RC1-3
- add patch to skip online test from
  https://github.com/phpredis/phpredis/pull/1304
- exclude s390x arch reported as
  https://github.com/phpredis/phpredis/issues/1305

* Wed Feb  7 2018 Remi Collet <remi@remirepo.net> - 4.0.0~RC1-1
- update to 4.0.0RC1
- rename to php-pecl-redis4
- enable lzf support
- update configuration for new options

* Wed Jan  3 2018 Remi Collet <remi@remirepo.net> - 3.1.6-1
- Update to 3.1.6

* Thu Dec 21 2017 Remi Collet <remi@remirepo.net> - 3.1.5-1
- update to 3.1.5 (stable)

* Mon Dec 11 2017 Remi Collet <remi@remirepo.net> - 3.1.5~RC2-1
- update to 3.1.5RC2 (beta)

* Fri Dec  1 2017 Remi Collet <remi@remirepo.net> - 3.1.5~RC1-1
- update to 3.1.5RC1 (beta)

* Sun Nov  5 2017 Remi Collet <remi@remirepo.net> - 3.1.4-3
- add upstream patch, fix segfault with PHP 5.x

* Tue Oct 17 2017 Remi Collet <remi@remirepo.net> - 3.1.4-2
- rebuild

* Wed Sep 27 2017 Remi Collet <remi@remirepo.net> - 3.1.4-1
- update to 3.1.4 (stable)

* Wed Sep 13 2017 Remi Collet <remi@remirepo.net> - 3.1.4~RC3-1
- update to 3.1.4RC3 (beta)

* Wed Sep 13 2017 Remi Collet <remi@remirepo.net> - 3.1.4~RC2-1
- update to 3.1.4RC2 (beta)
- open https://github.com/phpredis/phpredis/issues/1236
  unwanted noise (warning) not even using the extension

* Mon Sep  4 2017 Remi Collet <remi@remirepo.net> - 3.1.4~RC1-1
- update to 3.1.4RC1 (beta)

* Tue Jul 18 2017 Remi Collet <remi@remirepo.net> - 3.1.3-2
- rebuild for PHP 7.2.0beta1 new API

* Mon Jul 17 2017 Remi Collet <remi@remirepo.net> - 3.1.3-1
- update to 3.1.3 (stable)

* Tue Jun 27 2017 Remi Collet <remi@remirepo.net> - 3.1.3~RC2-1
- update to 3.1.3RC2 (beta)

* Wed Jun 21 2017 Remi Collet <remi@remirepo.net> - 3.1.3~RC1-2
- rebuild for 7.2.0alpha2

* Thu Jun  1 2017 Remi Collet <remi@remirepo.net> - 3.1.3~RC1-1
- update to 3.1.3RC1 (beta)

* Sat Mar 25 2017 Remi Collet <remi@remirepo.net> - 3.1.2-1
- Update to 3.1.2 (stable)

* Wed Feb  1 2017 Remi Collet <remi@fedoraproject.org> - 3.1.1-1
- Update to 3.1.1 (stable)

* Tue Jan 17 2017 Remi Collet <remi@fedoraproject.org> - 3.1.1-0.2.RC2
- Update to 3.1.1RC2

* Thu Dec 22 2016 Remi Collet <remi@fedoraproject.org> - 3.1.1-0.1.RC1
- test build for open upcoming 3.1.1RC1

* Wed Dec 21 2016 Remi Collet <remi@fedoraproject.org> - 3.1.1-0
- test build for open upcoming 3.1.1

* Thu Dec 15 2016 Remi Collet <remi@fedoraproject.org> - 3.1.0-2
- test build for open upcoming 3.1.1
- open https://github.com/phpredis/phpredis/issues/1060 broken impl
  with https://github.com/phpredis/phpredis/pull/1064
- reed https://github.com/phpredis/phpredis/issues/1062 session php 7.1
  with https://github.com/phpredis/phpredis/pull/1063

* Thu Dec 15 2016 Remi Collet <remi@fedoraproject.org> - 3.1.0-1
- update to 3.1.0
- open https://github.com/phpredis/phpredis/issues/1052 max version
- open https://github.com/phpredis/phpredis/issues/1053 segfault
- open https://github.com/phpredis/phpredis/issues/1054 warnings
- open https://github.com/phpredis/phpredis/issues/1055 reflection
- open https://github.com/phpredis/phpredis/issues/1056 32bits tests

* Thu Dec  1 2016 Remi Collet <remi@fedoraproject.org> - 3.0.0-3
- rebuild with PHP 7.1.0 GA

* Wed Sep 14 2016 Remi Collet <remi@fedoraproject.org> - 3.0.0-2
- rebuild for PHP 7.1 new API version

* Sat Jun 11 2016 Remi Collet <remi@fedoraproject.org> - 3.0.0-1
- Update to 3.0.0 (stable)

* Thu Jun  9 2016 Remi Collet <remi@fedoraproject.org> - 3.0.0-0.1.20160603git6447940
- refresh and bump version

* Thu May  5 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.6.20160504gitad3c116
- refresh

* Thu Mar  3 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.5.20160215git2887ad1
- enable igbinary support

* Fri Feb 19 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.4.20160215git2887ad1
- refresh

* Thu Feb 11 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.3.20160208git0d4b421
- refresh

* Tue Jan 26 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.2.20160125git7b36957
- refresh

* Sun Jan 10 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.2.20160106git4a37e47
- improve package.xml, set stability=devel

* Sun Jan 10 2016 Remi Collet <remi@fedoraproject.org> - 2.2.8-0.1.20160106git4a37e47
- update to 2.2.8-dev for PHP 7
- use git snapshot

* Sat Jun 20 2015 Remi Collet <remi@fedoraproject.org> - 2.2.7-2
- allow build against rh-php56 (as more-php56)

* Tue Mar 03 2015 Remi Collet <remi@fedoraproject.org> - 2.2.7-1
- Update to 2.2.7 (stable)
- drop runtime dependency on pear, new scriptlets

* Wed Dec 24 2014 Remi Collet <remi@fedoraproject.org> - 2.2.5-5.1
- Fedora 21 SCL mass rebuild

* Fri Oct  3 2014 Remi Collet <rcollet@redhat.com> - 2.2.5-5
- fix segfault with igbinary serializer
  https://github.com/nicolasff/phpredis/issues/341

* Mon Aug 25 2014 Remi Collet <rcollet@redhat.com> - 2.2.5-4
- improve SCL build

* Wed Apr 16 2014 Remi Collet <remi@fedoraproject.org> - 2.2.5-3
- add numerical prefix to extension configuration file (php 5.6)
- add comment about session configuration

* Thu Mar 20 2014 Remi Collet <rcollet@redhat.com> - 2.2.5-2
- fix memory corruption with PHP 5.6
  https://github.com/nicolasff/phpredis/pull/447

* Wed Mar 19 2014 Remi Collet <remi@fedoraproject.org> - 2.2.5-1
- Update to 2.2.5

* Wed Mar 19 2014 Remi Collet <rcollet@redhat.com> - 2.2.4-3
- allow SCL build

* Fri Feb 28 2014 Remi Collet <remi@fedoraproject.org> - 2.2.4-2
- cleaups
- move doc in pecl_docdir

* Mon Sep 09 2013 Remi Collet <remi@fedoraproject.org> - 2.2.4-1
- Update to 2.2.4

* Tue Apr 30 2013 Remi Collet <remi@fedoraproject.org> - 2.2.3-1
- update to 2.2.3
- upstream moved to pecl, rename from php-redis to php-pecl-redis

* Tue Sep 11 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-5.git6f7087f
- more docs and improved description

* Sun Sep  2 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-4.git6f7087f
- latest snahot (without bundled igbinary)
- remove chmod (done upstream)

* Sat Sep  1 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-3.git5df5153
- run only test suite with redis > 2.4

* Fri Aug 31 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-2.git5df5153
- latest master
- run test suite

* Wed Aug 29 2012 Remi Collet <remi@fedoraproject.org> - 2.2.2-1
- update to 2.2.2
- enable ZTS build

* Tue Aug 28 2012 Remi Collet <remi@fedoraproject.org> - 2.2.1-1
- initial package
