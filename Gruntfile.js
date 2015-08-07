module.exports = function(grunt) {

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
            files: ['<%= jshint.files %>', 'src/**/*.html', 'src/**/*.css'],
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
                        src: ['**/*.html', '**/*.css', 'favicon.ico'],
                        dest: 'webapp/',
                        filter: 'isFile'
                    }
                ]
            }
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
    // grunt.loadNpmTasks('grunt-contrib-uglify');

    // Default task(s).
    grunt.registerTask('default', ['jshint', 'concat', 'copy']);
    grunt.registerTask('dev', ['default', 'watch']);

};
