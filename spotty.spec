%define name spotty
%define version 0.2.0
%define unmangled_version 0.2.0
%define unmangled_version 0.2.0
%define release 1

Summary: Spotify Linux desktop integration
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPL-3
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Pami Ketolainen <pami.ketolainen@gmail.com>
Url: https://github.com/keto/spotty
BuildRequires: python-setuptools
Requires: python-setuptools
Requires: dbus-python
Requires: spotify-client-qt >= 1:0.6
    

%description
UNKNOWN

%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
install -m 755 -d %{buildroot}/%{_datadir}
install spotty.png %{buildroot}/%{_datadir}/pixmaps
install spotty.desktop %{buildroot}/%{_datadir}/applications

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
