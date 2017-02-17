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
var ngAnnotate = require('gulp-ng-annotate');
var uglify = require('gulp-uglify');
var git = require('git-rev');
var htmlmin = require('gulp-htmlmin');
var templateCache = require('gulp-angular-templatecache');
var addStream = require('add-stream');

var pkg = require('./package.json');

var paths = {
  scripts: ['./src-angular/**/*.js'],
  index_pages: ['./src-angular/*.html'],
  templates: ['./src-angular/**/*.html', '!./src-angular/*.html'],
  statics: ['./src-angular/**/*.svg', './src-angular/**/*.png', './src-angular/favicon.ico'],
  styles: ['./src-angular/**/*.less'],
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

gulp.task('concat', function (cb) {
  git.long(function (rev) {
    var stream = gulp.src(paths.scripts)
      .pipe(addStream.obj(prepareTemplates()))
      .pipe(sourcemaps.init())
        .pipe(ngAnnotate())
        .pipe(concat(pkg.name + '.js'))
        .pipe(preprocess({
          context: { VERSION: pkg.version, COMMIT_HASH: rev }
        }))
        .pipe(uglify())
      .pipe(sourcemaps.write('.'))
      .pipe(gulp.dest(path.join(paths.dest, 'scripts')))
      .on('end', cb);
  });
});

gulp.task('copy', function () {
  return gulp.src(paths.statics, {base: './src'})
    .pipe(gulp.dest(paths.dest));
});

function prepareTemplates() {
  return gulp.src(paths.templates)
    .pipe(htmlmin({collapseWhitespace: true}))
    .pipe(templateCache({module: 'monitorrent'}));
}

gulp.task('templateCache', function () {
  return prepareTemplates()
    .pipe(gulp.dest(paths.dest));
});

gulp.task('less', function () {
  return gulp.src(paths.styles)
    .pipe(less())
    .pipe(concat(pkg.name + '.css'))
    .pipe(gulp.dest(path.join(paths.dest, 'styles')));
});

gulp.task('copy-index', ['copy-index-html', 'copy-login-html']);

function preprocessIndexHtmlTpl(mode, rev) {
  return gulp.src(['./src-angular/index.html'])
    .pipe(preprocess({
      context: { VERSION: pkg.version, MODE: mode, COMMIT_HASH: rev }
    }))
    .pipe(rename(mode + '.html'))
    .pipe(gulp.dest(paths.dest));
}

gulp.task('copy-index-html', function (cb) {
  git.long(function (rev) {
    var stream = preprocessIndexHtmlTpl('index', rev);
    stream.on('end', cb);
  });
});

gulp.task('copy-login-html', function (cb) {
  git.long(function (rev) {
    var stream = preprocessIndexHtmlTpl('login', rev);
    stream.on('end', cb);
  });
});

gulp.task('watch', ['default'], function () {
  gulp.watch(paths.statics,                         ['copy']);
  gulp.watch(paths.scripts.concat(paths.templates), ['concat']);
  gulp.watch(paths.styles,                          ['less']);
  gulp.watch(paths.index_pages,                     ['copy-index']);
});

gulp.task('release', ['dist'], function () {
  return gulp.src([paths.release + '/**/*.*'])
    .pipe(zip(pkg.name + '-' + pkg.version + '.zip'))
    .pipe(gulp.dest('.'));
});

gulp.task('dist', ['clean-release', 'copy-python', 'copy-webapp', 'copy-desc']);

gulp.task('copy-python', function () {
  return gulp.src(['./**/*.py', '!./tests*/**/*.*', '!./' + paths.release + '/**/*.py'])
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
