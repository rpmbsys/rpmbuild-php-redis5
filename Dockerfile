ARG centos=7.8.2003
ARG image=php-msgpack-7.1

FROM aursu/peclbuild:${centos}-${image}

RUN yum -y --enablerepo=bintray-custom install \
        redis \
        liblzf-devel \
        libzstd-devel \
    && yum clean all && rm -rf /var/cache/yum

COPY SOURCES ${BUILD_TOPDIR}/SOURCES
COPY SPECS ${BUILD_TOPDIR}/SPECS

RUN chown -R $BUILD_USER ${BUILD_TOPDIR}/{SOURCES,SPECS}

USER $BUILD_USER

ENTRYPOINT ["/usr/bin/rpmbuild", "php-pecl-redis5.spec"]
CMD ["-ba"]
