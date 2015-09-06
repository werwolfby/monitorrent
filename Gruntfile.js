module.exports = function (grunt) {

    // Project configuration.
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        jshint: {
            files: ['src/**/*.js'],
            options: {
                globals: {
                    jQuery: true,
                    console: true,
                    module: true,
                    document: true
                }
            }
        },
        watch: {
            files: ['<%= jshint.files %>', 'src/**/*.html', 'src/**/*.less'],
            tasks: ['default']
        },
        concat: {
            options: {
                // define a string to put between each file in the concatenated output
                separator: ';'
            },
            dist: {
                // the files to concatenate
                src: ['src/**/*.js'],
                // the location of the resulting JS file
                dest: 'webapp/scripts/<%= pkg.name %>.js'
            }
        },
        copy: {
            main: {
                files: [
                    {
                        expand: true,
                        cwd: 'src/',
                        src: ['**/*.html', '**/*.svg', '**/*.png', 'favicon.ico'],
                        dest: 'webapp/',
                        filter: 'isFile'
                    }
                ]
            }
        },
        targethtml: {
            dist: {
                options: {
                    curlyTags: {
                        version: '<%= pkg.version %>'
                    }
                },
                files: {
                    'webapp/index.html': 'src/index.html',
                    'webapp/login.html': 'src/login.html'
                }
            }
        },
        less: {
            development: {
                options: {
                    paths: ["src/styles"]
                },
                files: {
                    "webapp/styles/monitorrent.css": "src/**/*.less"
                }
            },
            // production: {
            //     options: {
            //         paths: ["src/styles"],
            //         plugins: [
            //             new (require('less-plugin-autoprefix'))({ browsers: ["last 2 versions"] }),
            //             new (require('less-plugin-clean-css'))(cleanCssOptions)
            //         ],
            //         modifyVars: {
            //             imgPath: '"http://mycdn.com/path/to/images"',
            //             bgColor: 'red'
            //         }
            //     },
            //     files: {
            //         "webapp/styles/monitorrent.css": "**/*.less"
            //     }
            // }
        },
        // uglify: {
        //     options: {
        //         // the banner is inserted at the top of the output
        //         banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
        //     },
        //     dist: {
        //         files: {
        //             'dist/<%= pkg.name %>.min.js': ['<%= concat.dist.dest %>']
        //         }
        //     }
        // }
    });

    // Load the plugins
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-targethtml');
    grunt.loadNpmTasks('grunt-contrib-less');
    // grunt.loadNpmTasks('grunt-contrib-uglify');

    // Default task(s).
    grunt.registerTask('default', ['jshint', 'concat', 'less:development', 'copy', 'targethtml:dist']);
    grunt.registerTask('dev', ['default', 'watch']);

};
