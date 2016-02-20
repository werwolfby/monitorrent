var path = require('path');
var del = require('del');

var gulp = require('gulp');
var jshint = require('gulp-jshint');
var concat = require('gulp-concat');
var sourcemaps = require('gulp-sourcemaps');
var less = require('gulp-less');
var preprocess = require('gulp-preprocess');
var zip = require('gulp-zip');

var pkg = require('./package.json');

var paths = {
  scripts: ['./src/**/*.js'],
  index_pages: ['./src/*.html'],
  statics: ['./src/**/*.html', './src/**/*.svg', './src/**/*.png', './src/favicon.ico', '!./src/*.html'],
  styles: ['./src/**/*.less'],
  dest: 'webapp',
  release: 'dist'
};

gulp.task('default', ['clean', 'jshint', 'concat', 'copy', 'less', 'preprocess']);

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

gulp.task('preprocess', function () {
  return gulp.src(['./src/*.html'])
    .pipe(preprocess({
      context: { VERSION: pkg.version }
    }))
    .pipe(gulp.dest(paths.dest));
});

gulp.task('watch', ['default'], function () {
  gulp.watch(paths.statics,     ['copy']);
  gulp.watch(paths.scripts,     ['concat']);
  gulp.watch(paths.styles,      ['less']);
  gulp.watch(paths.index_pages, ['preprocess']);
});

gulp.task('release', ['clean-release', 'copy-python', 'copy-webapp', 'copy-desc'], function () {
  return gulp.src([paths.release + '/**/*.*'])
    .pipe(zip(pkg.name + '-' + pkg.version + '.zip'))
    .pipe(gulp.dest('.'));
});

gulp.task('copy-python', function () {
  return gulp.src(['./**/*.py', '!./monitorrent/tests/*.*', '!./monitorrent/tests_functional/*.*', '!./' + paths.release + '/**/*.py'])
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
