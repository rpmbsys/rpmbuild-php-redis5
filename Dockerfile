ARG os=10.0.20250606
ARG image=php-msgpack-8.4

FROM aursu/peclbuild:${os}-${image}

RUN dnf -y --enablerepo=bintray-custom install \
        redis \
        liblzf-devel \
        libzstd-devel \
        lz4-devel \
    && dnf clean all && rm -rf /var/cache/dnf

COPY SOURCES ${BUILD_TOPDIR}/SOURCES
COPY SPECS ${BUILD_TOPDIR}/SPECS

RUN chown -R $BUILD_USER ${BUILD_TOPDIR}/{SOURCES,SPECS}

USER $BUILD_USER

ENTRYPOINT ["/usr/bin/rpmbuild", "php-pecl-redis5.spec"]
CMD ["-ba"]
