# Changelog

## [1.2.0](https://github.com/LIT-Tools/lit/compare/v0.1.0...v1.2.0) (2025-03-22)


### Features

* easy start ([a67a3a8](https://github.com/LIT-Tools/lit/commit/a67a3a8a6d88205ca9a246e0c9f5182e8e1a3717))

## 0.1.0 (2025-03-21)


### ⚠ BREAKING CHANGES

* release

### Features

* add validations and notification for task format ([f4a9caa](https://github.com/LIT-Tools/lit/commit/f4a9caaa00b845b0aff626e1ab0e16494cdd213f))
* added automatic register increment for tasks ([6fe76ee](https://github.com/LIT-Tools/lit/commit/6fe76eeb3b335382ad11712e2bc57d8d74717205))
* added display of task hints by part of the number ([b3badbc](https://github.com/LIT-Tools/lit/commit/b3badbcde23010ff28c1b0be6e8f17b0796f1db6))
* added greeting in interactive mode ([38d61b9](https://github.com/LIT-Tools/lit/commit/38d61b9a4606ede6b18f60db089a0c8ef6f563a7))
* added hint for partial command input ([da69668](https://github.com/LIT-Tools/lit/commit/da6966897f8904a5d0885fd617a9f6c7ecf5161e))
* added logs commenting function ([4748f4e](https://github.com/LIT-Tools/lit/commit/4748f4e0c95adfb32120c1332940ca100c83cc55))
* added notification about non-standard task start time ([19f643e](https://github.com/LIT-Tools/lit/commit/19f643eb9c54eba83c9452fa02f69575a5dd07db))
* added output of the application version ([7531f42](https://github.com/LIT-Tools/lit/commit/7531f42512feec89ab0f82bf960cc63b83856c3c))
* added pull command with jira and gitlab keys ([139d699](https://github.com/LIT-Tools/lit/commit/139d69984a47beeacbe76127880d7857b73826d2))
* added support for minutes ([f9dad1c](https://github.com/LIT-Tools/lit/commit/f9dad1c5b244902529ffb3b3792d591a65b4bd74))
* added the init command to generate the configuration file ([48112ef](https://github.com/LIT-Tools/lit/commit/48112ef3eeb259827d57c819a54abcc57ed0d588))
* **cli:** add autocomplete ([4304786](https://github.com/LIT-Tools/lit/commit/4304786ba02632037d4e16da5501cc6245a850cf))
* **cli:** add push method ([47134bb](https://github.com/LIT-Tools/lit/commit/47134bb0174653b86467c8ad7aafb0801ba33d7a))
* **cli:** formed the image of the basic functionality ([13b1ca5](https://github.com/LIT-Tools/lit/commit/13b1ca530af589b7040d7294bbcf55b47d8f4eb8))
* **cli:** now the parameters Code, Hours and Message are only in short form ([a96c4de](https://github.com/LIT-Tools/lit/commit/a96c4de1d4cfa3a3aed5418af639c02b87114fca))
* easy start ([52ce3d7](https://github.com/LIT-Tools/lit/commit/52ce3d74e848df0d1f9d659a1954dd01a1fb31a7))
* implemented sending logs via the push method and writing results to the .lithistory file ([9d2204a](https://github.com/LIT-Tools/lit/commit/9d2204af8d3799895f64c46d15b2f777b305eef2))
* Initial commit 🎉 ([8dd3303](https://github.com/LIT-Tools/lit/commit/8dd33038d38836fa64895f4aa1d462639bb8bf8e))
* keys are read after the message ([774b519](https://github.com/LIT-Tools/lit/commit/774b519f5aac7ed9245ce46c22fee18bdb806548))
* now autocompletion for tasks also searches in the title ([32dc80c](https://github.com/LIT-Tools/lit/commit/32dc80c92311e91e755cb4e9bc6f92cd61d165d2))
* now autocompletion of commands depends on input ([17d4c4b](https://github.com/LIT-Tools/lit/commit/17d4c4be405f1545b625ad98abd0345e8d87cb49))
* now the status command shows the clock ([b9f0e5b](https://github.com/LIT-Tools/lit/commit/b9f0e5bbbd60e9127826d25595e11d81032c657e))
* now you can call the editor to change the prepared logs ([7fc34d5](https://github.com/LIT-Tools/lit/commit/7fc34d5575fce26dce04d7478c7fead2dc045ab2))
* the function of reading commit messages from a file has been implemented ([9d3daee](https://github.com/LIT-Tools/lit/commit/9d3daeeb01dc57d05cc72c0cbac9af422791d449))
* the function of reading tasks from a file has been implemented ([80df839](https://github.com/LIT-Tools/lit/commit/80df839ea7a032aeb923920cbb50689c67db71d3))


### Bug Fixes

* autocomplete ([c2ebb73](https://github.com/LIT-Tools/lit/commit/c2ebb732981d83d234ca63b18b0c73fae958fefc))
* **config:** [HACK] wrapped reading of the config in a function so that it does not crash on the init command ([ce4642c](https://github.com/LIT-Tools/lit/commit/ce4642c170030ffbc0180d7c5e7512b735987056))
* fixed an error when entering a comment with an unclosed quotation mark ([c2e3a52](https://github.com/LIT-Tools/lit/commit/c2e3a52bf91f5edc976fb59c3791e7d66d8564ab))
* fixed search for tasks, previously fresh ones were not found ([e27096c](https://github.com/LIT-Tools/lit/commit/e27096c28e1baca531544bf998ce48b22b1a99b9))
* fixed the output of logs, now it is correctly sorted ([526acad](https://github.com/LIT-Tools/lit/commit/526acad06ecd6f99c9352b533446b4ceb37fa70e))
* fixed time comparison during validation ([dc7b743](https://github.com/LIT-Tools/lit/commit/dc7b743bc4b267ec638d80550a3d66ffdfc0d76e))
* fixed time format when writing to the sending log ([26db4c4](https://github.com/LIT-Tools/lit/commit/26db4c4a96c080c882b0a54572edc9988644eb78))
* now keys are not shown instead of message ([cc4b179](https://github.com/LIT-Tools/lit/commit/cc4b1793a1eb8248711ccd4528cee6659224e4d0))
* now you can use working time syntax like jira ([1996cb3](https://github.com/LIT-Tools/lit/commit/1996cb3877d071696481193b99020f4dcf69d659))
* replaced exit() with return when token is empty ([3dd197b](https://github.com/LIT-Tools/lit/commit/3dd197be94cf7677a5397881159e92bdfec9d63f))


### Documentation

* added development plans to README ([90f1ea8](https://github.com/LIT-Tools/lit/commit/90f1ea852b04750bba1b955ea613acfa5ec7c202))
* added name and logo ([5e7761d](https://github.com/LIT-Tools/lit/commit/5e7761de850f757bfe3f4c868591c0b53890f7d7))
* added planned functionality to README ([d57617d](https://github.com/LIT-Tools/lit/commit/d57617d79ac5a80b182338008afbb23f3b9ef0cc))
* corrected typo in example ([bb44033](https://github.com/LIT-Tools/lit/commit/bb4403318cccb38d47537581369096413acad8e6))
* fix examples ([0e155d2](https://github.com/LIT-Tools/lit/commit/0e155d21d042672e9a8859f872e6a41aaea33804))
* MIT license ([9e98da6](https://github.com/LIT-Tools/lit/commit/9e98da67766499e89b39d940747dde0b1373b345))
* Release v1.0.0 ([00dddd4](https://github.com/LIT-Tools/lit/commit/00dddd4a3157027c19f1b9f46dd5f8adb2ac52eb))
* revised installation instructions for Mac and Windows ([91bc144](https://github.com/LIT-Tools/lit/commit/91bc1446656ea9522aac3a01c48fc4cbfa4f429e))
* reworked README file ([d8c1a35](https://github.com/LIT-Tools/lit/commit/d8c1a35bada7c0a037ad9c5db5faa014ba7ae423))
