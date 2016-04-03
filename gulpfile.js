var path = require('path');
var del = require('del');

var gulp = require('gulp');
var jshint = require('gulp-jshint');
var concat = require('gulp-concat');
var sourcemaps = require('gulp-sourcemaps');
var less = require('gulp-less');
var preprocess = require('gulp-preprocess');
var zip = require('gulp-zip');
var rename = require('gulp-rename');

var pkg = require('./package.json');

var paths = {
  scripts: ['./src/**/*.js'],
  index_pages: ['./src/*.html'],
  statics: ['./src/**/*.html', './src/**/*.svg', './src/**/*.png', './src/favicon.ico'],
  styles: ['./src/**/*.less'],
  dest: 'webapp',
  release: 'dist'
};

gulp.task('default', ['clean', 'jshint', 'concat', 'copy', 'less', 'copy-index']);

gulp.task('clean', function () {
  return del.sync([paths.dest]);
});

gulp.task('clean-release', function () {
  return del.sync([paths.release]);
});

gulp.task('jshint', function () {
  return gulp.src(paths.scripts)
    .pipe(jshint())
    .pipe(jshint.reporter('default'));
});

gulp.task('concat', function () {
  return gulp.src(paths.scripts)
    .pipe(sourcemaps.init())
      .pipe(concat(pkg.name + '.js'))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(path.join(paths.dest, 'scripts')));
});

gulp.task('copy', function () {
  return gulp.src(paths.statics, {base: './src'})
    .pipe(gulp.dest(paths.dest));
});

gulp.task('less', function () {
  return gulp.src(paths.styles)
    .pipe(less())
    .pipe(concat(pkg.name + '.css'))
    .pipe(gulp.dest(path.join(paths.dest, 'styles')));
});

gulp.task('copy-index', ['copy-index-html', 'copy-login-html']);

function preprocessIndexHtmlTpl(mode) {
  return gulp.src(['./src/index.html.tpl'])
    .pipe(preprocess({
      context: { VERSION: pkg.version, MODE: mode }
    }))
    .pipe(rename(mode + '.html'))
    .pipe(gulp.dest(paths.dest));
}

gulp.task('copy-index-html', function () {
  return preprocessIndexHtmlTpl('index');
});

gulp.task('copy-login-html', function () {
  return preprocessIndexHtmlTpl('login');
});

gulp.task('watch', ['default'], function () {
  gulp.watch(paths.statics,     ['copy']);
  gulp.watch(paths.scripts,     ['concat']);
  gulp.watch(paths.styles,      ['less']);
  gulp.watch(paths.index_pages, ['copy-index']);
});

gulp.task('release', ['dist'], function () {
  return gulp.src([paths.release + '/**/*.*'])
    .pipe(zip(pkg.name + '-' + pkg.version + '.zip'))
    .pipe(gulp.dest('.'));
});

gulp.task('dist', ['clean-release', 'copy-python', 'copy-webapp', 'copy-desc']);

gulp.task('copy-python', function () {
  return gulp.src(['./**/*.py', '!./monitorrent/tests/**/*.*', '!./monitorrent/tests_functional/*.*', '!./' + paths.release + '/**/*.py'])
    .pipe(gulp.dest(paths.release));
});

gulp.task('copy-webapp', ['default'], function () {
  return gulp.src([path.join(paths.dest, '**/*.*'), '!./**/*.map'])
    .pipe(gulp.dest(path.join(paths.release, paths.dest)));
});

gulp.task('copy-desc', function () {
  return gulp.src(['./package.json', './README.md', './requirements.txt'])
    .pipe(gulp.dest(paths.release));
})
