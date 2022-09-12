// Base
const path = require('path');
const gulp = require('gulp');
const notify = require('gulp-notify');
const plumber = require('gulp-plumber');

// General
const concat = require('gulp-concat');
const sourcemaps = require('gulp-sourcemaps');
const named = require('vinyl-named');
const browserSync = require('browser-sync').create();
// Scripts
const webpack = require('webpack')
const webpackStream = require('webpack-stream');

// Styles
const sass = require('gulp-sass');
const autoprefixer = require('gulp-autoprefixer');

// Images
const tinypng = require('gulp-tinypng-compress');
const svgSprite = require('gulp-svg-sprites');
const replace = require('gulp-replace');
const cheerio = require('gulp-cheerio');
const base64 = require('gulp-base64');

// Jade
const pug = require('gulp-pug');

// webp
const webp = require('gulp-webp');

function browsersync() {
    browserSync.init({
        notify: false, //Отключаем уведомления
        proxy: "localhost:8000" //Перенаправляем на джангу
    });
}

// Paths
const paths = {
    build: path.join(__dirname, '.'),
    node: path.join(__dirname, 'node_modules'),
    src: {
        self: path.join(__dirname, 'src'),
        js: 'src/js/',
        sass: 'src/scss/',
        images: 'src/images/',
        pug: 'src/jade/',
    },
    static: {
        self: 'static/',
        js: 'static/js/',
        css: 'static/css/',
        images: 'static/images/',
    },
    html: './templates/layout'
}

function jsTask() {
    return gulp
        .src([
            path.join(paths.src.js, "pages", "*.js"),
        ])
        .pipe(named())
        .pipe(webpackStream({
            mode: "development",
            output: {
                path: paths.build,
                publicPath: "/",
                filename: "static/js/[name].bundle.js",
                library: "[name]"
            },
            module: {
                rules: [
                    {
                        test: /\.(js|jsx)$/,
                        exclude: /node_modules/,
                        use: {
                            loader: 'babel-loader',
                            options: {
                                presets: ['@babel/preset-env'],
                                plugins: [
                                    ['@babel/plugin-proposal-class-properties'],
                                    ['@babel/plugin-transform-runtime'],
                                ]
                            }
                        }
                    },
                ]
            },
            resolve: {
                extensions: ["*", ".js", ".jsx"],
                modules: [
                    paths.node,
                    paths.src.self,
                ],
                alias: {
                    'jquery': paths.node + '/jquery/dist/jquery.js',
                }
            },
            plugins: [
                new webpack.ProvidePlugin({
                    $: "jquery",
                    jQuery: "jquery",
                })
            ]
        }))
        .pipe(gulp.dest(paths.build));
}

gulp.task(jsTask);


function jsBuildTask() {
    return gulp
        .src([
                path.join(paths.src.js, "pages", "*.js"),
            ]
        )
        .pipe(named())
        .pipe(webpackStream({
            mode: "production",
            output: {
                path: paths.build,
                publicPath: "/",
                filename: "static/js/[name].bundle.js",
                library: "[name]"
            },
            module: {
                rules: [
                    {
                        test: /\.(js|jsx)$/,
                        exclude: /node_modules/,
                        use: {
                            loader: 'babel-loader',
                            options: {
                                presets: ['@babel/preset-env'],
                                plugins: [
                                    ['@babel/plugin-proposal-class-properties'],
                                    ['@babel/plugin-transform-runtime'],
                                ]
                            }
                        }
                    },
                ]
            },
            resolve: {
                extensions: ["*", ".js", ".jsx"],
                modules: [
                    paths.node,
                    paths.src.self,
                ],
                alias: {
                    'jquery': paths.node + '/jquery/dist/jquery.js',
                }
            },
            // optimization: {
            //     splitChunks: {
            //         cacheGroups: {
            //             commons: {
            //                 test: /[\\/](node_modules|vendors)[\\/]/,
            //                 name: "vendors",
            //                 chunks: "all"
            //             }
            //         }
            //     }
            // },
            plugins: [
                new webpack.ProvidePlugin({
                    $: "jquery",
                    jQuery: "jquery",
                })
            ]
        }))
        .pipe(gulp.dest(paths.build));
}

gulp.task(jsBuildTask);


function sassTask() {
    // Libs
    gulp
        .src([
            // path.join(paths.node,       "@fancyapps/fancybox/dist/jquery.fancybox.css"),
            path.join(paths.node, 'ion-rangeslider/css/*.css'),
            path.join(paths.src.sass, "vendors/*.+(scss|sass)"),
        ])
        .pipe(plumber({errorHandler: notify.onError("<%= error.message %>")}))
        .pipe(sass({outputStyle: "compressed"}).on("error", sass.logError))
        .pipe(autoprefixer("last 2 version"))
        .pipe(concat("vendors.min.css"))
        .pipe(gulp.dest(paths.static.css))


    // Styles
    return gulp
        .src(path.join(paths.src.sass, "pages/*.scss"))
        .pipe(plumber({errorHandler: notify.onError("<%= error.message %>")}))
        .pipe(sourcemaps.init())
        .pipe(sass().on("error", sass.logError))
        .pipe(base64({
            baseDir: '/static/test',
            extensions: ['svg', 'png', /\.jpg#datauri$/i],
            exclude: [/\.server\.(com|net)\/dynamic\//, '--live.jpg'],
            maxImageSize: 32 * 1024, // bytes
            debug: false
        }))
        .pipe(autoprefixer("last 2 version"))
        .pipe(sourcemaps.write("./", {sourceRoot: "/src/scss"}))
        .pipe(gulp.dest(paths.static.css))
}

gulp.task(sassTask);


function sassBuildTask() {
    return gulp
        .src(path.join(paths.src.sass, "pages/*.scss"))
        .pipe(plumber({errorHandler: notify.onError("<%= error.message %>")}))
        .pipe(sass({outputStyle: "compressed"}).on("error", sass.logError))
        .pipe(base64({
            baseDir: '/static/test',
            extensions: ['svg', 'png', /\.jpg#datauri$/i],
            exclude: [/\.server\.(com|net)\/dynamic\//, '--live.jpg'],
            maxImageSize: 32 * 1024, // bytes
            debug: false
        }))
        .pipe(autoprefixer("last 2 version"))
        .pipe(gulp.dest(paths.static.css))
}

gulp.task(sassBuildTask);


function tinypngTask() {
    return gulp
        .src(paths.src.images + '/*.{png,jpg,jpeg}')
        .pipe(tinypng({
            key: 'odthLyLlVCQlfl9KLbpWcDBGEAqaBK8T',
            sigFile: paths.static.images + '/.tinypng-sigs'
        }))
        .pipe(gulp.dest(paths.static.images))
}

gulp.task(tinypngTask);


function webpTask() {
    return gulp
        .src(paths.src.images + '/webp/*.{png,jpg,jpeg}')
        .pipe(webp())
        .pipe(gulp.dest(paths.static.images))
}

gulp.task(webpTask);


function svgTask() {
    return gulp
        .src(paths.src.images + '/*.svg')
        .pipe(cheerio({
            run: function ($) {
                $('[fill]').removeAttr('fill');
                $('[stroke]').removeAttr('stroke');
                $('[style]').removeAttr('style');
            },
            parserOptions: {xmlMode: true}
        }))
        .pipe(replace('&gt;', '>'))
        .pipe(
            svgSprite({
                    mode: "symbols",
                    preview: false,
                    selector: "%f",
                    svg: {
                        symbols: 'sprite.svg'
                    },
                    transformData: function (data, config) {
                        for (var i in data.svg) {
                            var result = data.svg[i].data.match(/path id="([a-z]+)"/ig);
                            if (null !== result) {
                                for (var j in result) {
                                    var regexp = /\"([a-z]+)\"/i;
                                    var matches = regexp.exec(result[j]);
                                    matches[0] = matches[0].replace(/\"/g, '');

                                    var k = 0;

                                    var regexp = new RegExp('(path id\=\"|xlink\:href\=\"#)(' + matches[0] + '){1}', 'g');
                                    data.svg[i].data = data.svg[i].data.replace(regexp, function (str, p1, p2, offset, s) {
                                        return p1 + "" + i + "" + j + "" + p2;
                                    });
                                }
                            }
                        }
                        return data;
                    },
                }
            ))
        .pipe(replace('NaN ', '-'))
        .pipe(gulp.dest(paths.static.images))
}

gulp.task(svgTask);


function staticSvgTask() {
    return gulp
        .src(paths.src.images + '/static/*.svg')
        .pipe(replace('&gt;', '>'))
        .pipe(
            svgSprite({
                    mode: "symbols",
                    preview: false,
                    selector: "%f",
                    svg: {
                        symbols: 'static-sprite.svg'
                    },
                    transformData: function (data, config) {
                        for (var i in data.svg) {
                            var result = data.svg[i].data.match(/path id="([a-z]+)"/ig);
                            if (null !== result) {
                                for (var j in result) {
                                    var regexp = /\"([a-z]+)\"/i;
                                    var matches = regexp.exec(result[j]);
                                    matches[0] = matches[0].replace(/\"/g, '');

                                    var k = 0;

                                    var regexp = new RegExp('(path id\=\"|xlink\:href\=\"#)(' + matches[0] + '){1}', 'g');
                                    data.svg[i].data = data.svg[i].data.replace(regexp, function (str, p1, p2, offset, s) {
                                        return p1 + "" + i + "" + j + "" + p2;
                                    });
                                }
                            }
                        }
                        return data;
                    },
                }
            ))
        .pipe(replace('NaN ', '-'))
        .pipe(gulp.dest(paths.static.images))
}

gulp.task(staticSvgTask);


function pugTask() {
    return gulp
        .src(paths.src.pug + '/*.pug')
        .pipe(plumber({errorHandler: notify.onError("<%= error.message %>")}))
        .pipe(pug({pretty: '\t'}))
        .pipe(gulp.dest(paths.html))
}

gulp.task(pugTask);

function reload(done) {
    browserSync.reload();
    done();
}

gulp.task(reload);

function watchTask() {

    browsersync();
    gulp.watch(path.join(paths.src.pug + '/*.pug'), gulp.parallel(pugTask));

    gulp.watch(path.join(paths.src.js, "**/*.+(js|ts)"), gulp.series(jsTask, reload));
    gulp.watch(path.join(paths.src.sass, "**/*.+(scss|sass)"), gulp.series(sassTask, reload));

    gulp.watch(paths.src.images + '/*.{png,jpg,jpeg}', gulp.parallel(tinypngTask));
    gulp.watch(paths.src.images + '/webp/*.{png,jpg,jpeg}', gulp.parallel(webpTask));
    gulp.watch(paths.src.images + '*.svg', gulp.parallel(svgTask));
    gulp.watch(paths.src.images + '/static/*.svg', gulp.parallel(staticSvgTask));
    gulp.watch('**/*.{html}').on('change', browserSync.reload);
    return gulp
}

gulp.task(watchTask);



gulp.task('default', gulp.parallel(watchTask, pugTask, jsTask, sassTask, tinypngTask, webpTask, svgTask, staticSvgTask));
gulp.task('build', gulp.parallel(jsBuildTask, sassBuildTask));