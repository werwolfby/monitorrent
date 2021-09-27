const path = require('path');
const del = require('del');

const gulp = require('gulp');
const jshint = require('gulp-jshint');
const concat = require('gulp-concat');
const sourcemaps = require('gulp-sourcemaps');
const less = require('gulp-less');
const preprocess = require('gulp-preprocess');
const zip = require('gulp-zip');
const rename = require('gulp-rename');
const ngAnnotate = require('gulp-ng-annotate');
const uglify = require('gulp-uglify');
const git = require('git-rev');
const htmlmin = require('gulp-htmlmin');
const templateCache = require('gulp-angular-templatecache');
const addStream = require('add-stream');

const pkg = require('./package.json');

const paths = {
  scripts: ['./src/**/*.js'],
  index_pages: ['./src/*.html'],
  templates: ['./src/**/*.html', '!./src/*.html'],
  statics: ['./src/**/*.svg', './src/**/*.png', './src/favicon.ico'],
  styles: ['./src/**/*.less'],
  dest: 'webapp',
  release: 'dist'
};

gulp.task('clean', function () {
  return del([paths.dest]);
});

gulp.task('clean-release', function () {
  return del([paths.release]);
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

gulp.task('copy-index', gulp.parallel('copy-index-html', 'copy-login-html'));

gulp.task('default', gulp.series('clean', 'jshint', 'concat', 'copy', 'less', 'copy-index'));

function preprocessIndexHtmlTpl(mode, rev) {
  return gulp.src(['./src/index.html'])
    .pipe(preprocess({
      context: { VERSION: pkg.version, MODE: mode, COMMIT_HASH: rev }
    }))
    .pipe(rename(mode + '.html'))
    .pipe(gulp.dest(paths.dest));
}

gulp.task('watch', gulp.series('default', function () {
  gulp.watch(paths.statics,                         ['copy']);
  gulp.watch(paths.scripts.concat(paths.templates), ['concat']);
  gulp.watch(paths.styles,                          ['less']);
  gulp.watch(paths.index_pages,                     ['copy-index']);
}));

gulp.task('copy-python', function () {
  return gulp.src(['./**/*.py', '!./tests*/**/*.*', '!./venv/**/*.*', '!./' + paths.release + '/**/*.py'])
    .pipe(gulp.dest(paths.release));
});

gulp.task('copy-webapp', gulp.series('default', function () {
  return gulp.src([path.join(paths.dest, '**/*.*'), '!./**/*.map'])
    .pipe(gulp.dest(path.join(paths.release, paths.dest)));
}));

gulp.task('copy-desc', function () {
  return gulp.src(['./package.json', './README.md', './requirements.txt'])
    .pipe(gulp.dest(paths.release));
})

gulp.task('dist', gulp.series('clean-release', gulp.parallel('copy-python', 'copy-webapp', 'copy-desc')));

gulp.task('release', gulp.series('dist', function () {
  return gulp.src([paths.release + '/**/*.*'])
    .pipe(zip(pkg.name + '-' + pkg.version + '.zip'))
    .pipe(gulp.dest('.'));
}));
