# centos/sclo spec file for php-pecl-mongodb, from:
#
# remirepo spec file for php-pecl-mongodb
#
# Copyright (c) 2015-2019 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%if 0%{?scl:1}
%global sub_prefix %{scl_prefix}
%if "%{scl}" == "rh-php70"
%global sub_prefix sclo-php70-
%endif
%if "%{scl}" == "rh-php71"
%global sub_prefix sclo-php71-
%endif
%if "%{scl}" == "rh-php72"
%global sub_prefix sclo-php72-
%endif
%if "%{scl}" == "rh-php73"
%global sub_prefix sclo-php73-
%endif
%scl_package       php-pecl-mongodb
%endif

%global pecl_name  mongodb
%global ini_name   50-%{pecl_name}.ini

Summary:        MongoDB driver for PHP
Name:           %{?sub_prefix}php-pecl-%{pecl_name}
Version:        1.5.4
Release:        1%{?dist}
License:        ASL 2.0
Group:          Development/Languages
URL:            http://pecl.php.net/package/%{pecl_name}
Source0:        http://pecl.php.net/get/%{pecl_name}-%{version}%{?prever}.tgz

BuildRequires:  %{?scl_prefix}php-devel > 5.5
BuildRequires:  %{?scl_prefix}php-pear
BuildRequires:  %{?scl_prefix}php-json
BuildRequires:  cyrus-sasl-devel
BuildRequires:  openssl-devel
BuildRequires:  snappy-devel
BuildRequires:  zlib-devel
%if 0%{?rhel} >= 7
BuildRequires:  libicu-devel
%endif


Requires:       %{?scl_prefix}php(zend-abi) = %{php_zend_api}
Requires:       %{?scl_prefix}php(api) = %{php_core_api}
Requires:       %{?scl_prefix}php-json%{?_isa}

Provides:       bundled(libbson) = 1.13.0
Provides:       bundled(mongo-c-driver) = 1.13.0

# Don't provide php-mongodb which is the pure PHP library
Provides:       %{?scl_prefix}php-pecl(%{pecl_name})         = %{version}
Provides:       %{?scl_prefix}php-pecl(%{pecl_name})%{?_isa} = %{version}
%if "%{?scl_prefix}" != "%{?sub_prefix}"
Provides:       %{?scl_prefix}php-pecl-%{pecl_name}          = %{version}-%{release}
Provides:       %{?scl_prefix}php-pecl-%{pecl_name}%{?_isa}  = %{version}-%{release}
%endif

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter shared private
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
The purpose of this driver is to provide exceptionally thin glue between
MongoDB and PHP, implementing only fundemental and performance-critical
components necessary to build a fully-functional MongoDB driver.

Package built for PHP %(%{__php} -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')%{?scl: as Software Collection (%{scl} by %{?scl_vendor}%{!?scl_vendor:rh})}.


%prep
%setup -q -c
mv %{pecl_name}-%{version}%{?prever} NTS

# Don't install/register tests
sed -e 's/role="test"/role="src"/' \
    %{?_licensedir:-e '/LICENSE/s/role="doc"/role="src"/' } \
    -i package.xml

cd NTS

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_MONGODB_VERSION /{s/.* "//;s/".*$//;p}' phongo_version.h)
if test "x${extver}" != "x%{version}%{?prever:%{prever}}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}%{?prever:%{prever}}.
   exit 1
fi
cd ..

# Create configuration file
cat << 'EOF' | tee %{ini_name}
; Enable %{summary} extension module
extension=%{pecl_name}.so

; Configuration
;mongodb.debug=''
EOF


%build
peclbuild() {
  %{_bindir}/${1}ize

  %configure \
    --with-php-config=%{_bindir}/${1}-config \
    --enable-mongodb-crypto-system-profile \
    --with-mongodb-sasl=cyrus \
%if 0%{?rhel} >= 7
    --with-mongodb-icu=yes \
%endif
    --with-mongodb-ssl=openssl \
    --enable-mongodb

  make %{?_smp_mflags}
}

cd NTS
peclbuild php


%install
make -C NTS \
     install INSTALL_ROOT=%{buildroot}

# install config file
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

# Documentation
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


# when pear installed alone, after us
%triggerin -- %{?scl_prefix}php-pear
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

# posttrans as pear can be installed after us
%posttrans
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

%postun
if [ $1 -eq 0 -a -x %{__pecl} ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%check
OPT="-n"
[ -f %{php_extdir}/json.so ] && OPT="$OPT -d extension=json.so"

: Minimal load test for NTS extension
%{__php} $OPT \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}

# mongodb-server not available in base repository
# so can't run upstream test suite


%files
%{?_licensedir:%license NTS/LICENSE}
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so


%changelog
* Tue Jun  4 2019 Remi Collet <remi@remirepo.net> - 1.5.4-1
- update to 1.5.4

* Fri Sep 21 2018 Remi Collet <remi@remirepo.net> - 1.5.3-1
- update to 1.5.3
- with libbson and libmongoc 1.13.0

* Fri Aug 17 2018 Remi Collet <remi@remirepo.net> - 1.5.2-1
- update to 1.5.2
- with libbson and libmongoc 1.12.0

* Mon Jul  9 2018 Remi Collet <remi@remirepo.net> - 1.5.1-1
- update to 1.5.1

* Tue Jun 26 2018 Remi Collet <remi@remirepo.net> - 1.5.0-1
- update to 1.5.0
- with libbson and libmongoc 1.11.0
- add dependency on icu

* Thu Jun  7 2018 Remi Collet <remi@remirepo.net> - 1.4.4-1
- Update to 1.4.4

* Thu Apr 19 2018 Remi Collet <remi@remirepo.net> - 1.4.3-1
- Update to 1.4.3

* Wed Mar  7 2018 Remi Collet <remi@remirepo.net> - 1.4.2-1
- Update to 1.4.2 (no change)
- with libbson and libmongoc 1.9.3

* Fri Feb  9 2018 Remi Collet <remi@remirepo.net> - 1.4.0-1
- update to 1.4.0 with libbson and libmongoc 1.9.2
- enable snappy and zlib compression
- build with --enable-mongodb-crypto-system-profile option

* Mon Dec  4 2017 Remi Collet <remi@remirepo.net> - 1.3.4-1
- update to 1.3.4

* Wed Nov 22 2017 Remi Collet <remi@remirepo.net> - 1.3.3-1
- update to 1.3.3 with libbson and libmongoc 1.8.2

* Tue Oct 31 2017 Remi Collet <remi@remirepo.net> - 1.3.2-1
- Update to 1.3.2

* Tue Oct 17 2017 Remi Collet <remi@remirepo.net> - 1.3.1-1
- update to 1.3.1 with libbson and libmongoc 1.8.1

* Wed Sep 20 2017 Remi Collet <remi@remirepo.net> - 1.3.0-1
- update to 1.3.0 with libbson and libmongoc 1.8.0

* Fri Sep  8 2017 Remi Collet <remi@remirepo.net> - 1.2.10-1
- update to 1.2.10

* Thu Aug 10 2017 Remi Collet <remi@remirepo.net> - 1.2.9-2
- change for sclo-php71

* Tue May  9 2017 Remi Collet <remi@remirepo.net> - 1.2.9-1
- update to 1.2.9

* Mon Apr 10 2017 Remi Collet <remi@fedoraproject.org> - 1.2.8-1
- update to 1.2.8
- add dependency on json extension

* Thu Dec  8 2016 Remi Collet <remi@fedoraproject.org> - 1.1.10-1
- update to 1.1.10

* Fri Nov  4 2016 Remi Collet <remi@fedoraproject.org> - 1.1.9-1
- cleanup for SCLo build
- use bundled libraries

* Fri Oct 21 2016 Remi Collet <remi@fedoraproject.org> - 1.1.9-1
- Update to 1.1.9 (no change)

* Wed Sep 14 2016 Remi Collet <remi@fedoraproject.org> - 1.1.8-5
- rebuild for PHP 7.1 new API version

* Tue Jul 19 2016 Remi Collet <remi@fedoraproject.org> - 1.1.8-4
- License is ASL 2.0, from review #1269056

* Wed Jul 06 2016 Remi Collet <remi@fedoraproject.org> - 1.1.8-2
- Update to 1.1.8

* Fri Jun  3 2016 Remi Collet <remi@fedoraproject.org> - 1.1.7-3
- run the test suite during the build (x86_64 only)
- ignore known to fail tests

* Thu Jun  2 2016 Remi Collet <remi@fedoraproject.org> - 1.1.7-2
- Update to 1.1.7

* Thu Apr  7 2016 Remi Collet <remi@fedoraproject.org> - 1.1.6-2
- Update to 1.1.6

* Thu Mar 31 2016 Remi Collet <remi@fedoraproject.org> - 1.1.5-4
- load after smbclient to workaround
  https://jira.mongodb.org/browse/PHPC-658

* Fri Mar 18 2016 Remi Collet <remi@fedoraproject.org> - 1.1.5-2
- Update to 1.1.5 (stable)

* Thu Mar 10 2016 Remi Collet <remi@fedoraproject.org> - 1.1.4-2
- Update to 1.1.4 (stable)

* Sat Mar  5 2016 Remi Collet <remi@fedoraproject.org> - 1.1.3-2
- Update to 1.1.3 (stable)

* Thu Jan 07 2016 Remi Collet <remi@fedoraproject.org> - 1.1.2-2
- Update to 1.1.2 (stable)

* Thu Dec 31 2015 Remi Collet <remi@fedoraproject.org> - 1.1.1-4
- fix patch for 32bits build
  open https://github.com/mongodb/mongo-php-driver/pull/191

* Sat Dec 26 2015 Remi Collet <remi@fedoraproject.org> - 1.1.1-2
- Update to 1.1.1 (stable)
- add patch for 32bits build,
  open https://github.com/mongodb/mongo-php-driver/pull/185

* Wed Dec 16 2015 Remi Collet <remi@fedoraproject.org> - 1.1.0-1
- Update to 1.1.0 (stable)
- raise dependency on libmongoc >= 1.3.0

* Tue Dec  8 2015 Remi Collet <remi@fedoraproject.org> - 1.0.1-2
- update to 1.0.1 (stable)
- ensure libmongoc >= 1.2.0 and < 1.3 is used

* Fri Oct 30 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-2
- update to 1.0.0 (stable)

* Tue Oct 27 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.5.RC0
- Update to 1.0.0RC0 (beta)

* Tue Oct  6 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.3-beta2
- Update to 1.0.0beta2 (beta)

* Fri Sep 11 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.2-beta1
- Update to 1.0.0beta1 (beta)

* Mon Aug 31 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.1.alpha2
- Update to 1.0.0alpha2 (alpha)
- buid with system libmongoc

* Thu May 07 2015 Remi Collet <remi@fedoraproject.org> - 0.6.3-1
- Update to 0.6.3 (alpha)

* Wed May 06 2015 Remi Collet <remi@fedoraproject.org> - 0.6.2-1
- Update to 0.6.2 (alpha)

* Wed May 06 2015 Remi Collet <remi@fedoraproject.org> - 0.6.0-1
- Update to 0.6.0 (alpha)

* Sat Apr 25 2015 Remi Collet <remi@fedoraproject.org> - 0.5.1-1
- Update to 0.5.1 (alpha)

* Thu Apr 23 2015 Remi Collet <remi@fedoraproject.org> - 0.5.0-2
- build with system libbson
- open https://jira.mongodb.org/browse/PHPC-259

* Wed Apr 22 2015 Remi Collet <remi@fedoraproject.org> - 0.5.0-1
- initial package, version 0.5.0 (alpha)

