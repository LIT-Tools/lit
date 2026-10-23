# Changelog

## [1.2.0](https://github.com/LIT-Tools/lit/compare/v1.1.0...v1.2.0) (2026-10-23)


### Features

* **calc_crap:** add report formats and CI threshold ([e22aa0e](https://github.com/LIT-Tools/lit/commit/e22aa0ec4eccbbf97e1bd6dceb6e4f2ca3f85c0b))
* **config:** add jira api_version and cloud token guidance ([4f5f022](https://github.com/LIT-Tools/lit/commit/4f5f022e4058a71729a4f13e1dfbaa5b69e509d3))
* **integrations:** add jira client factory with api version ([ab6eff2](https://github.com/LIT-Tools/lit/commit/ab6eff2583bc1cbcb2c263f87e4cee6bee969469))
* **integrations:** add plain_text_to_adf for Jira v3 ([e80a867](https://github.com/LIT-Tools/lit/commit/e80a867971c4fda7ad7220141619b1be139bd9f6))
* **integrations:** use ADF for worklog comment on Jira v3 ([14777d4](https://github.com/LIT-Tools/lit/commit/14777d4bd95b397ba8028dee639651bb53bfcac1))
* **jira:** migrate to Jira REST API v3 ([04357fa](https://github.com/LIT-Tools/lit/commit/04357fa6e7508f320bc2db50821aad9bf700192e))


### Bug Fixes

* **cli:** add entry-point wrapper that builds parser before calling main ([72dc7c4](https://github.com/LIT-Tools/lit/commit/72dc7c4a469c9a1397360f9b198809b29ac4a60e))
* **cli:** hint at quoted add message on parse error ([ea52c1a](https://github.com/LIT-Tools/lit/commit/ea52c1ad3d004cca10de127d9b4d934212ffcdc9))
* **cli:** resolve version in src layout and frozen builds ([0061198](https://github.com/LIT-Tools/lit/commit/0061198d9258d09c7577bc431d937ae83dc4da0d))
* **core:** repair tests and imports after step 3 refactoring ([aefc335](https://github.com/LIT-Tools/lit/commit/aefc33517e3a4550f286db92879daca8053f9f5e))
* finalize test alignment and audit checklist after Step D ([f507bb6](https://github.com/LIT-Tools/lit/commit/f507bb68dbb2b91e1107f4886e667afb36b1236d))
* **gitlab:** load commits from all branches ([eae11f1](https://github.com/LIT-Tools/lit/commit/eae11f1ab849cb51967f6946358423de690dee22))
* **integrations:** repair jira pull pagination and currentUser jql ([d38cafc](https://github.com/LIT-Tools/lit/commit/d38cafcfd0080a73b110cce8ca21741a45597ca0))
* make calc_crap work with src/ layout and tests/ ([7964de2](https://github.com/LIT-Tools/lit/commit/7964de2ed976178824d19b63943e7a9f2587e119))
* **pyinstaller:** update spec path to src/lit/__main__.py ([3be1e79](https://github.com/LIT-Tools/lit/commit/3be1e79f4a1299161f8f681e5ff992de4cfd32f4))
* restore zebrains defaults and drop author_username filter ([71653ea](https://github.com/LIT-Tools/lit/commit/71653eaed2b3d19ca6f26cbe2c11353d14ebc7a1))
* **validation:** handle invalid calendar dates gracefully ([9c7610b](https://github.com/LIT-Tools/lit/commit/9c7610bbd9d6e70da10fe5b2b70d76f736323917))


### Documentation

* actualize README for uv and src layout ([a89877b](https://github.com/LIT-Tools/lit/commit/a89877b986c0fd0e0e3037f7d9439ae9a4eb34b3))
* add agent documentation and git-commit-convention skill ([56dced8](https://github.com/LIT-Tools/lit/commit/56dced88e85fa4d6396b295779f44f7b2eeed0f6))
* add auto-update draft from dev ([494f1f0](https://github.com/LIT-Tools/lit/commit/494f1f05f29d85ae9a0a61c182e464fc7cc9e9b5))
* add Step 5 notes to refactoring log ([03f10b8](https://github.com/LIT-Tools/lit/commit/03f10b889f48e3130c7a12f84aa81ed3f639b20e))
* add Step 6 notes to refactoring log ([d81a11f](https://github.com/LIT-Tools/lit/commit/d81a11f6a4c62cc6431387839c5ef049ba0bbdad))
* consolidate refactoring docs and add Jira v3 plan ([f7d8b3d](https://github.com/LIT-Tools/lit/commit/f7d8b3df642831810f69b0fe6facb96bda3960cd))
* dedup PATH in Windows install ([4f36ebe](https://github.com/LIT-Tools/lit/commit/4f36ebebebedf25ed5895b6d382ae9474095fa57))
* fix badges, restore --branch and editor comment ([ccfa8a3](https://github.com/LIT-Tools/lit/commit/ccfa8a3cd92c7b67f8b5595baac2650b5a1e4148))
* **integrations:** explain sys.modules shims, plan their removal ([773f00d](https://github.com/LIT-Tools/lit/commit/773f00df6a6f3b0a5144973111b19feb64e4ffc1))
* **jira:** rewrite v3 plan and record spike ([6da1bc3](https://github.com/LIT-Tools/lit/commit/6da1bc32585bde3fe3d02589fe77c4761f874c18))
* **jira:** sanitize spike notes and mark migration complete ([8e53f26](https://github.com/LIT-Tools/lit/commit/8e53f269eda7a759bf26989f7374ed69eb70bdbf))
* **log:** add migration lessons from src/ move ([b8a6619](https://github.com/LIT-Tools/lit/commit/b8a66196931caa0dcbeb1edacde5717cd35502bc))
* **loop:** mark steps 1-3 as complete ([130e968](https://github.com/LIT-Tools/lit/commit/130e9689f840edcf196a42370b93d6616f9c929b))
* **refactoring:** add post-mortem for step 0 ([e5bc5f6](https://github.com/LIT-Tools/lit/commit/e5bc5f6b587be7b1500671f9ea1420e5b560f77a))
* **refactoring:** add post-mortem for step 1 ([d37e17a](https://github.com/LIT-Tools/lit/commit/d37e17a485fd67a5a9cde507dd6ee576f9b3de55))
* **refactoring:** add post-mortem for step 2 ([096b2a2](https://github.com/LIT-Tools/lit/commit/096b2a20fbc2346488d810b95eb15be7e7aea891))
* **refactoring:** add post-mortem for step 3 ([421f552](https://github.com/LIT-Tools/lit/commit/421f552b56f765b545efa3f83038a5ff148a4bef))
* **refactoring:** add Ralph Loop pipeline for incremental refactoring ([d04c88b](https://github.com/LIT-Tools/lit/commit/d04c88b42c45cc5f1786d5cf8effdb2f60c46fa5))
* **refactoring:** mark step 0 baseline as complete ([22af351](https://github.com/LIT-Tools/lit/commit/22af35110b8a16d888f29f5d76c7c58521166d41))
* restructure refactoring plan for src/ migration cycle ([830da7c](https://github.com/LIT-Tools/lit/commit/830da7c79b3742094a5ebb36523491375f7404f9))

## [1.1.0](https://github.com/LIT-Tools/lit/compare/v1.0.1...v1.1.0) (2025-04-06)


### Features

* ability to select a text editor has been added to the configuration ([83e169f](https://github.com/LIT-Tools/lit/commit/83e169fd07fbcaf0258bd024ddcb4f628650008b))


### Bug Fixes

* added leading zeros for date ([d1fefb4](https://github.com/LIT-Tools/lit/commit/d1fefb4d84b34499797ac09e9784cde06f1a4fc8)), closes [#60](https://github.com/LIT-Tools/lit/issues/60)
* fixed error when there was no custom editor in the config ([7a2c702](https://github.com/LIT-Tools/lit/commit/7a2c7022dad194efe06a06f33f330919c19a0c99))
* handle multiline logs input ([2a00bdb](https://github.com/LIT-Tools/lit/commit/2a00bdbdea6e7693d57c36ac70169de72ee87109)), closes [#61](https://github.com/LIT-Tools/lit/issues/61)
* now you can call help and check the version in interactive mode ([9518623](https://github.com/LIT-Tools/lit/commit/9518623eb66463af4e1a0cb94522187e01174723)), closes [#59](https://github.com/LIT-Tools/lit/issues/59)

## [1.0.1](https://github.com/LIT-Tools/lit/compare/v1.0.0...v1.0.1) (2025-03-22)


### Documentation

* added easy start example and fixed manual for install ([076dc4b](https://github.com/LIT-Tools/lit/commit/076dc4bc89badb4ce2a1eeedaa2de1f086f44252))
* fix license ([3021d85](https://github.com/LIT-Tools/lit/commit/3021d8591e427ea0afdd83089c4849edd4836df8))

## 1.0.0 (2025-03-22)


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
* easy install ([8e4e82a](https://github.com/LIT-Tools/lit/commit/8e4e82a5ac99d4c7bb2d81e4029aac5abc536a46))
* fix examples ([0e155d2](https://github.com/LIT-Tools/lit/commit/0e155d21d042672e9a8859f872e6a41aaea33804))
* MIT license ([9e98da6](https://github.com/LIT-Tools/lit/commit/9e98da67766499e89b39d940747dde0b1373b345))
* Release v1.0.0 ([00dddd4](https://github.com/LIT-Tools/lit/commit/00dddd4a3157027c19f1b9f46dd5f8adb2ac52eb))
* revised installation instructions for Mac and Windows ([91bc144](https://github.com/LIT-Tools/lit/commit/91bc1446656ea9522aac3a01c48fc4cbfa4f429e))
* reworked README file ([d8c1a35](https://github.com/LIT-Tools/lit/commit/d8c1a35bada7c0a037ad9c5db5faa014ba7ae423))
