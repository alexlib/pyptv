
START_TEST(test_trackcorr_no_add)
{
    tracking_run *run;
    int step;
    Calibration *calib[3];
    control_par *cpar;

    chdir("testing_fodder/track");
    copy_res_dir("res_orig/", "res/");
    copy_res_dir("img_orig/", "img/");
    
    printf("----------------------------\n");
    printf("Test tracking multiple files 2 cameras, 1 particle \n");
    cpar = read_control_par("parameters/ptv.par");
    read_all_calibration(calib, cpar->num_cams);
    
    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);
    run->tpar->add = 0;
    track_forward_start(run);
    trackcorr_c_loop(run, run->seq_par->first);
    
    for (step = run->seq_par->first + 1; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    empty_res_dir();
    
    int range = run->seq_par->last - run->seq_par->first;
    double npart, nlinks;
    
    /* average of all steps */
    npart = (double)run->npart / range;
    nlinks = (double)run->nlinks / range;
    
    ck_assert_msg(fabs(npart - 0.8)<EPS,
                  "Was expecting npart == 208/210 but found %f \n", npart);
    ck_assert_msg(fabs(nlinks - 0.8)<EPS,
                  "Was expecting nlinks == 198/210 but found %f \n", nlinks);
    
}
END_TEST

START_TEST(test_trackcorr_with_add)
{
    tracking_run *run;
    int step;
    Calibration *calib[3];
    control_par *cpar;

    chdir("testing_fodder/track");
    copy_res_dir("res_orig/", "res/");
    copy_res_dir("img_orig/", "img/");
    
    printf("----------------------------\n");
    printf("Test 2 cameras, 1 particle with add \n");
    cpar = read_control_par("parameters/ptv.par");
    read_all_calibration(calib, cpar->num_cams);
    
    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);

    run->seq_par->first = 10240;
    run->seq_par->last = 10250;
    run->tpar->add = 1;


    track_forward_start(run);
    trackcorr_c_loop(run, run->seq_par->first);
    
    for (step = run->seq_par->first + 1; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    empty_res_dir();
    
    int range = run->seq_par->last - run->seq_par->first;
    double npart, nlinks;
    
    /* average of all steps */
    npart = (double)run->npart / range;
    nlinks = (double)run->nlinks / range;
    
    ck_assert_msg(fabs(npart - 1.0)<EPS,
                  "Was expecting npart == 208/210 but found %f \n", npart);
    ck_assert_msg(fabs(nlinks - 0.7)<EPS,
                  "Was expecting nlinks == 328/210 but found %f \n", nlinks);
    
}
END_TEST

START_TEST(test_cavity)
{
    tracking_run *run;
    Calibration *calib[4];
    control_par *cpar;
    int step;
    struct stat st = {0};
    
    
    printf("----------------------------\n");
    printf("Test cavity case \n");
    
    chdir("testing_fodder/test_cavity");
    if (stat("res", &st) == -1) {
        mkdir("res", 0700);
    }
    copy_res_dir("res_orig/", "res/");
    
    if (stat("img", &st) == -1) {
        mkdir("img", 0700);
    }
    copy_res_dir("img_orig/", "img/");

    fail_if((cpar = read_control_par("parameters/ptv.par"))== 0);
    read_all_calibration(calib, cpar->num_cams);

    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);

    printf("num cams in run is %d\n",run->cpar->num_cams);
    printf("add particle is %d\n",run->tpar->add);

    track_forward_start(run);    
    for (step = run->seq_par->first; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    printf("total num parts is %d, num links is %d \n", run->npart, run->nlinks);

    ck_assert_msg(run->npart == 672+699+711,
                  "Was expecting npart == 2082 but found %d \n", run->npart);
    ck_assert_msg(run->nlinks == 132+176+144,
                  "Was expecting nlinks == 452 found %ld \n", run->nlinks);



    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);

    run->tpar->add = 1;
    printf("changed add particle to %d\n",run->tpar->add);

    track_forward_start(run);    
    for (step = run->seq_par->first; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    printf("total num parts is %d, num links is %d \n", run->npart, run->nlinks);

    ck_assert_msg(run->npart == 672+699+715,
                  "Was expecting npart == 2086 but found %d \n", run->npart);
    ck_assert_msg(run->nlinks == 132+180+149,
                  "Was expecting nlinks == 461 found %ld \n", run->nlinks);
    
    
    empty_res_dir();
}
END_TEST

START_TEST(test_burgers)
{
    tracking_run *run;
    Calibration *calib[4];
    control_par *cpar;
    int status, step;
    struct stat st = {0};


    printf("----------------------------\n");
    printf("Test Burgers vortex case \n");
    

    fail_unless((status = chdir("testing_fodder/burgers")) == 0);

    if (stat("res", &st) == -1) {
        mkdir("res", 0700);
    }
    copy_res_dir("res_orig/", "res/");
    
    if (stat("img", &st) == -1) {
        mkdir("img", 0700);
    }
    copy_res_dir("img_orig/", "img/");

    fail_if((cpar = read_control_par("parameters/ptv.par"))== 0);
    read_all_calibration(calib, cpar->num_cams);

    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);

    printf("num cams in run is %d\n",run->cpar->num_cams);
    printf("add particle is %d\n",run->tpar->add);

    track_forward_start(run);    
    for (step = run->seq_par->first; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    printf("total num parts is %d, num links is %d \n", run->npart, run->nlinks);

    ck_assert_msg(run->npart == 19,
                  "Was expecting npart == 19 but found %d \n", run->npart);
    ck_assert_msg(run->nlinks == 17,
                  "Was expecting nlinks == 17 found %ld \n", run->nlinks);



    run = tr_new_legacy("parameters/sequence.par", 
        "parameters/track.par", "parameters/criteria.par", 
        "parameters/ptv.par", calib);

    run->tpar->add = 1;
    printf("changed add particle to %d\n",run->tpar->add);

    track_forward_start(run);    
    for (step = run->seq_par->first; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    printf("total num parts is %d, num links is %d \n", run->npart, run->nlinks);

    ck_assert_msg(run->npart == 20,
                  "Was expecting npart == 20 but found %d \n", run->npart);
    ck_assert_msg(run->nlinks ==20,
                  "Was expecting nlinks == 20 but found %d \n", run->nlinks);
    
    empty_res_dir();

}
END_TEST

START_TEST(test_trackback)
{
    tracking_run *run;
    double nlinks;
    int step;
    Calibration *calib[3];
    control_par *cpar;
    
    chdir("testing_fodder/track");
    copy_res_dir("res_orig/", "res/");
    copy_res_dir("img_orig/", "img/");
    
    printf("----------------------------\n");
    printf("trackback test \n");
    
    cpar = read_control_par("parameters/ptv.par");
    read_all_calibration(calib, cpar->num_cams);
    run = tr_new_legacy("parameters/sequence.par",
        "parameters/track.par", "parameters/criteria.par",
        "parameters/ptv.par", calib);

    run->seq_par->first = 10240;
    run->seq_par->last = 10250;
    run->tpar->add = 1;

    track_forward_start(run);
    trackcorr_c_loop(run, run->seq_par->first);
    
    for (step = run->seq_par->first + 1; step < run->seq_par->last; step++) {
        trackcorr_c_loop(run, step);
    }
    trackcorr_c_finish(run, run->seq_par->last);
    run->tpar->dvxmin = run->tpar->dvymin = run->tpar->dvzmin = -50;
    run->tpar->dvxmax = run->tpar->dvymax = run->tpar->dvzmax = 50;
    run->lmax = norm((run->tpar->dvxmin - run->tpar->dvxmax), \
                     (run->tpar->dvymin - run->tpar->dvymax), \
                     (run->tpar->dvzmin - run->tpar->dvzmax));
    
    nlinks = trackback_c(run);
    empty_res_dir();
    
    // ck_assert_msg(fabs(nlinks - 1.043062)<EPS,
    //               "Was expecting nlinks to be 1.043062 but found %f\n", nlinks);
}
END_TEST

START_TEST(test_new_particle)
{
    /* this test also has the side-effect of testing instantiation of a 
       tracking_run struct without the legacy stuff. */

    Calibration *calib[3];
    control_par *cpar;
    sequence_par *spar;
    track_par *tpar;
    volume_par *vpar;
    tracking_run *run;
    
    char ori_tmpl[] = "cal/sym_cam%d.tif.ori";
    char added_name[] = "cal/cam1.tif.addpar";
    char ori_name[256];
    int cam, status;

    fail_unless((status = chdir("testing_fodder")) == 0);
    
    /* Set up all scene parameters to track one specially-contrived 
       trajectory. */
    for (cam = 0; cam < 3; cam++) {
        sprintf(ori_name, ori_tmpl, cam + 1);
        calib[cam] = read_calibration(ori_name, added_name, NULL);
    }
    
    fail_unless((status = chdir("track/")) == 0);
    copy_res_dir("res_orig/", "res/");
    copy_res_dir("img_orig/", "img/");

    spar = read_sequence_par("parameters/sequence_newpart.par", 3);
    cpar = read_control_par("parameters/control_newpart.par");
    tpar = read_track_par("parameters/track.par");
    vpar = read_volume_par("parameters/criteria.par");
    
    run = tr_new(spar, tpar, vpar, cpar, 4, MAX_TARGETS, 
        "res/particles", "res/linkage", "res/whatever", calib, 0.1);

    tpar->add = 0;
    track_forward_start(run);
    trackcorr_c_loop(run, 10001);
    trackcorr_c_loop(run, 10002);
    trackcorr_c_loop(run, 10003);
    trackcorr_c_loop(run, 10004);
    
    fb_prev(run->fb); /* because each loop step moves the FB forward */
    fail_unless(run->fb->buf[3]->path_info[0].next == -2);
    printf("next is %d\n",run->fb->buf[3]->path_info[0].next );
    
    tpar->add = 1;
    track_forward_start(run);
    trackcorr_c_loop(run, 10001);
    trackcorr_c_loop(run, 10002);
    trackcorr_c_loop(run, 10003);
    trackcorr_c_loop(run, 10004);
    
    fb_prev(run->fb); /* because each loop step moves the FB forward */
    fail_unless(run->fb->buf[3]->path_info[0].next == 0);
    printf("next is %d\n",run->fb->buf[3]->path_info[0].next );
    empty_res_dir();
}
END_TEST