        s1 = st.session_state.student1
        s2 = st.session_state.student2
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج", key="logout_btn"):
                logout()
        
        st.markdown(f'<div class="card"><h3>ملف الطالب</h3><p>الطالب الأول: <b style="color:#2F6F7E;">{s1["لقب"] if "لقب" in s1 else s1["اللقب"]} {s1["الإسم"] if "الإسم" in s1 else s1["إسم"]}</b></p><p>التخصص: <b>{s1["التخصص"]}</b></p></div>', unsafe_allow_html=True)
        if s2 is not None: st.markdown(f'<div class="card"><p>الطالب الثاني: <b style="color:#2F6F7E;">{s2["لقب"] if "لقب" in s2 else s2["اللقب"]} {s2["الإسم"] if "الإسم" in s2 else s2["إسم"]}</b></p></div>', unsafe_allow_html=True)

        # تبويبات الطالب
        tab_memo, tab_notify = st.tabs(["مذكرتي", "الإشعارات والطلبات"])

        with tab_memo:
            if st.session_state.mode == "view":
                df_memos_fresh = load_memos()
                note_num = str(s1.get('رقم المذكرة', '')).strip()
                memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_num]
                if not memo_info.empty:
                    memo_info = memo_info.iloc[0]
                    st.markdown(f'''<div class="card" style="border-left: 5px solid #FFD700;">
                        <h3>✅ أنت مسجل في المذكرة التالية:</h3>
                        <p><b>رقم المذكرة:</b> {memo_info['رقم المذكرة']}</p>
                        <p><b>العنوان:</b> {memo_info['عنوان المذكرة']}</p>
                        <p><b>المشرف:</b> {memo_info['الأستاذ']}</p>
                        <p><b>التخصص:</b> {memo_info['التخصص']}</p>
                        <p><b>التاريخ:</b> {memo_info.get('تاريخ التسجيل','')}</p>
                    </div>''', unsafe_allow_html=True)

            elif st.session_state.mode == "register":
                st.markdown('<div class="card"><h3>تسجيل مذكرة جديدة</h3></div>', unsafe_allow_html=True)
                all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
                selected_prof = st.selectbox("اختر الأستاذ المشرف:", [""] + all_profs)
                
                if selected_prof:
                    student_specialty = s1["التخصص"]
                    prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()]
                    reg_count = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
                    
                    if reg_count >= 4:
                        st.error(f'❌ الأستاذ {selected_prof} استنفذ كل العناوين')
                    else:
                        avail_memos = df_memos[
                            (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                            (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                            (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
                        ][["رقم المذكرة", "عنوان المذكرة"]]
                        
                        if not avail_memos.empty:
                            st.success(f'✅ المذكرات المتاحة في تخصصك ({student_specialty}):')
                            for _, row in avail_memos.iterrows():
                                st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                        else:
                            st.error('لا توجد مذكرات متاحة ❌')
                
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1: st.session_state.note_number = st.text_input("رقم المذكرة", value=st.session_state.note_number)
                with c2: st.session_state.prof_password = st.text_input("كلمة سر المشرف", type="password")

                if not st.session_state.show_confirmation:
                    if st.button("المتابعة للتأكيد"):
                        if not st.session_state.note_number or not st.session_state.prof_password: st.error("⚠️ يرجى إدخال البيانات")
                        else: st.session_state.show_confirmation = True; st.rerun()
                else:
                    st.warning(f"⚠️ تأكيد التسجيل - المذكرة رقم: {st.session_state.note_number}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("تأكيد نهائي", type="primary"):
                            valid, prof_row, err = verify_professor_password(st.session_state.note_number, st.session_state.prof_password, df_memos, df_prof_memos)
                            if not valid: st.error(err); st.session_state.show_confirmation = False
                            else:
                                with st.spinner('⏳ جاري تسجيل...'):
                                    success, msg = update_registration(st.session_state.note_number, s1, s2)
                                if success: st.success(msg); st.balloons(); clear_cache_and_reload(); st.session_state.mode = "view"; st.session_state.show_confirmation = False; time.sleep(2); st.rerun()
                                else: st.error(msg); st.session_state.show_confirmation = False
                    with col2:
                        if st.button("إلغاء"): st.session_state.show_confirmation = False; st.rerun()

        with tab_notify:
            st.subheader("تنبيهات خاصة بك")
            my_memo_id = str(s1.get('رقم المذكرة', '')).strip()
            if my_memo_id:
                my_reqs = df_requests[df_requests["رقم المذكرة"].astype(str).str.strip() == my_memo_id]
                if not my_reqs.empty:
                    for _, r in my_reqs.iterrows():
                        req_type = r['نوع الطلب']
                        details = str(r.get('العنوان الجديد', r.get('المبررات', ''))).strip()
                        
                        # القواعد: إخفاء المبررات في حذف طالب والتنازل
                        show_details = True
                        if req_type in ["حذف طالب", "تنازل"]:
                            show_details = False

                        st.markdown(f"""
                        <div class='card' style='border-right: 4px solid #F59E0B; padding: 20px;'>
                            <h4>{req_type}</h4>
                            <p>التاريخ: {r['الوقت']}</p>
                            <p>الحالة: <b>{r['الحالة']}</b></p>
                            {'<p>التفاصيل: ' + details + '</p>' if show_details else '<p><i>التفاصيل مخفية</i></p>'}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("لا توجد تنبيهات جديدة.")
            else:
                st.info("يجب تسجيل مذكرة أولاً لتلقي التنبيهات.")

# ============================================================
# فضاء الأساتذة (تصميم جديد)
# ============================================================
elif st.session_state.user_type == "professor":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_prof"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>فضاء الأساتذة</h2>", unsafe_allow_html=True)
        
        with st.form("prof_login_form"):
            c1, c2 = st.columns(2)
            with c1: u = st.text_input("اسم المستخدم")
            with c2: p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول"):
                v, r = verify_professor(u, p, df_prof_memos)
                if not v: st.error(r)
                else: st.session_state.professor = r; st.session_state.logged_in = True; st.rerun()
    else:
        prof = st.session_state.professor
        p_name = prof["الأستاذ"]
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        
        st.markdown(f"<h2 style='margin-bottom:20px;'>فضاء الأستاذ <span style='color:#FFD700;'>{p_name}</span></h2>", unsafe_allow_html=True)

        prof_memos = df_memos[df_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
        total = len(prof_memos)
        registered = len(prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        available = total - registered
        is_exhausted = registered >= 4

        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{total}</div>
                <div class="kpi-label">إجمالي المذكرات</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{registered}</div>
                <div class="kpi-label">المذكرات المسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{available}</div>
                <div class="kpi-label">المذكرات المتاحة</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if is_exhausted:
            st.markdown('<div class="alert-card">لقد استنفذت العناوين الأربعة المخصصة لك.</div>', unsafe_allow_html=True)
        
        # --- Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(["المذكرات المسجلة", "كلمات السر", "التنبيهات", "المتاحة/المقترحة"])
        
        with tab1:
            st.subheader("المذكرات المسجلة")
            
            # منطق الصفحة المنبثقة (Modal) مقابل القائمة
            if st.session_state.get('selected_memo'):
                # عرض صفحة التفاصيل فقط
                sel_mid = st.session_state.selected_memo
                sel_memo = prof_memos[prof_memos["رقم المذكرة"] == sel_mid].iloc[0]
                
                st.empty() # إخفاء القائمة الرئيسية مؤقتاً
                st.markdown("<div class='card' style='border: 2px solid #2F6F7E;'><h2>🔧 تفاصيل وإدارة المذكرة</h2></div>", unsafe_allow_html=True)
                
                # زر العودة
                col1, col2, col3 = st.columns([1, 6, 1])
                with col1:
                    if st.button("⬅ عودة للقائمة"):
                        del st.session_state.selected_memo
                        st.rerun()

                # معلومات الطلاب والإيميلات
                s1_name = sel_memo['الطالب الأول']
                s2_name = sel_memo.get('الطالب الثاني', '')
                
                # جلب الإيميلات
                s1_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 1', ''), s1_name, df_students)
                s2_email = get_student_email(sel_memo.get('رقم تسجيل الطالب 2', ''), s2_name, df_students) if s2_name else ""
                
                st.markdown(f"""
                <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                    <h4>الطالب الأول: {s1_name}</h4>
                    {f"<p style='color:#10B981;'>📧 {s1_email}</p>" if s1_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                </div>
                """, unsafe_allow_html=True)
                
                if s2_name:
                    st.markdown(f"""
                    <div style='background:#1E293B; padding:15px; border-radius:10px; margin-bottom:15px;'>
                        <h4>الطالب الثاني: {s2_name}</h4>
                        {f"<p style='color:#10B981;'>📧 {s2_email}</p>" if s2_email else "<p style='color:#EF4444;'>لا يوجد إيميل</p>"}
                    </div>
                    """, unsafe_allow_html=True)

                # شريط التقدم
                progress_val = str(sel_memo.get('نسبة التقدم', '0')).strip()
                try: prog_int = int(progress_val) if progress_val else 0
                except: prog_int = 0
                
                st.markdown(f"<div class='progress-container'><div class='progress-bar' style='width: {prog_int}%;'></div></div>", unsafe_allow_html=True)

                # التحكم في التقدم
                new_prog = st.selectbox("تحديث نسبة التقدم:", [
                    "0%", "10% - ضبط المقدمة", "30% - الفصل الأول", 
                    "60% - الفصل الثاني", "80% - الخاتمة", "100% - مكتملة"
                ], key=f"np_{sel_mid}")
                if st.button("حفظ التقدم", key=f"sv_{sel_mid}"):
                    mapping = {"0%":0, "10% - ضبط المقدمة":10, "30% - الفصل الأول":30, "60% - الفصل الثاني":60, "80% - الخاتمة":80, "100% - مكتملة":100}
                    s, m = update_progress(sel_mid, mapping[new_prog])
                    st.success(m) if s else st.error(m); time.sleep(1); st.rerun()

                st.markdown("---")
                st.markdown("### 📨 تقديم طلب جديد")
                
                # نظام الطلبات
                req_op = st.selectbox("نوع الطلب:", ["", "تغيير عنوان المذكرة", "حذف طالب (ثنائية)", "إضافة طالب (فردية)", "تنازل عن الإشراف"], key=f"req_{sel_mid}")
                
                details_to_save = ""
                validation_error = None
                
                if req_op == "تغيير عنوان المذكرة":
                    new_title = st.text_input("العنوان الجديد:", key=f"nt_{sel_mid}")
                    if st.button("إرسال طلب تغيير العنوان", key=f"btn_ch_{sel_mid}"):
                        if new_title: details_to_save = f"العنوان الجديد المقترح: {new_title}"
                        else: validation_error = "الرجاء إدخال العنوان"
                            
                elif req_op == "حذف طالب (ثنائية)":
                    if not s2_name: st.warning("هذه مذكرة فردية!")
                    else:
                        st.write("الطالبان:")
                        st.write(f"1. {s1_name}")
                        st.write(f"2. {s2_name}")
                        to_del = st.selectbox("اختر الطالب للحذف:", ["", "الطالب الأول", "الطالب الثاني"], key=f"del_{sel_mid}")
                        just = st.text_area("تبريرات الحذف:", key=f"jus_del_{sel_mid}")
                        if st.button("إرسال طلب الحذف", key=f"btn_del_{sel_mid}"):
                            if to_del and just: details_to_save = f"حذف: {to_del}. السبب: {just}"
                            else: validation_error = "اكمل البيانات"
                            
                elif req_op == "إضافة طالب (فردية)":
                    if s2_name: st.warning("هذه مذكرة ثنائية بالفعل!")
                    else:
                        reg_to_add = st.text_input("رقم التسجيل:", key=f"add_{sel_mid}")
                        if st.button("تحقق وإرسال", key=f"btn_add_{sel_mid}"):
                            target = df_students[df_students["رقم التسجيل"] == reg_to_add]
                            if target.empty: validation_error = "رقم التسجيل غير موجود"
                            elif target.iloc[0].get("رقم المذكرة"): validation_error = "الطالب لديه مذكرة بالفعل"
                            elif target.iloc[0].get("التخصص") != sel_memo['التخصص']: validation_error = "التخصص غير متطابق"
                            else:
                                just = st.text_area("ملاحظات (اختياري):", key=f"jus_add_{sel_mid}")
                                details_to_save = f"إضافة الطالب المسجل: {reg_to_add}. ملاحظات: {just}"
                                
                elif req_op == "تنازل عن الإشراف":
                    just = st.text_area("مبررات التنازل:", key=f"res_{sel_mid}")
                    if st.button("إرسال طلب التنازل", key=f"btn_res_{sel_mid}"):
                        if just: details_to_save = f"التنازل عن الإشراف. المبررات: {just}"
                        else: validation_error = "الرجاء كتابة المبررات"

                # تنفيذ الطلب
                if validation_error:
                    st.error(validation_error)
                elif details_to_save:
                    suc, msg = save_and_send_request(p_name, sel_mid, sel_memo['عنوان المذكرة'], req_op, details_to_save)
                    if suc: st.success(msg); time.sleep(1); st.rerun()
                    else: st.error(msg)

            else:
                # عرض القائمة (List View)
                registered_memos = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
                
                if not registered_memos.empty:
                    cols = st.columns(2)
                    for i, (_, memo) in enumerate(registered_memos.iterrows()):
                        with cols[i % 2]:
                            mid = memo['رقم المذكرة']
                            title = memo['عنوان المذكرة']
                            
                            st.markdown(f"""
                            <div class="card" style="border-right: 5px solid #10B981;">
                                <h4>{mid} - {title}</h4>
                                <p style="color:#94A3B8; font-size:0.9em;">تخصص: {memo['التخصص']}</p>
                                <p style="font-size:0.8em; color:#2F6F7E;">انقر على الزر بالأسفل للتفاصيل</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # زر يفتح الصفحة المنبثقة
                            if st.button("⚙️ إدارة وتفاصيل", key=f"mgr_{mid}"):
                                st.session_state.selected_memo = mid
                                st.rerun()
                else:
                    st.info("لا توجد مذكرات مسجلة حتى الآن.")

        with tab2:
            st.subheader("كلمات السر")
            pwds = df_prof_memos[df_prof_memos["الأستاذ"].astype(str).str.strip() == prof_name.strip()]
            if not pwds.empty:
                for _, row in pwds.iterrows():
                    stat = str(row.get("تم التسجيل", "")).strip()
                    pwd = str(row.get("كلمة سر التسجيل", "")).strip()
                    if pwd:
                        color = "#10B981" if stat == "نعم" else "#F59E0B"
                        status_txt = "مستخدمة" if stat == "نعم" else "متاحة"
                        st.markdown(f'''
                        <div class="card" style="border-right: 5px solid {color}; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h3 style="margin:0; font-family:monospace; font-size:1.8rem; color:#FFD700;">{pwd}</h3>
                                <p style="margin:5px 0 0 0 0; color:#94A3B8;">الحالة: {status_txt}</p>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            else: st.info("لا توجد كلمات سر مسندة إليك.")

        with tab3:
            st.subheader("إشعاراتي")
            my_reqs = df_requests[df_requests["الأستاذ"] == p_name]
            if not my_reqs.empty:
                for _, r in my_reqs.iterrows():
                    status_color = "#10B981" if r['الحالة'] == "مقبول" else "#F59E0B"
                    st.markdown(f"""
                    <div class="card" style="border-right: 4px solid {status_color};">
                        <h4>{r['نوع الطلب']} - {r['رقم المذكرة']}</h4>
                        <p>التاريخ: {r['الوقت']}</p>
                        <p>الحالة: <b>{r['الحالة']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("لا توجد إشعارات")

        with tab4:
            if is_exhausted: st.subheader("💡 المذكرات المقترحة")
            else: st.subheader("⏳ المذكرات المتاحة للتسجيل")
            
            avail = prof_memos[prof_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            if not avail.empty:
                for _, m in avail.iterrows():
                    st.markdown(f"""
                    <div class="card" style="border-left: 4px solid #64748B;">
                        <h4>{m['رقم المذكرة']}</h4>
                        <p>{m['عنوان المذكرة']}</p>
                        <p style="color:#94A3B8;">تخصص: {m['التخصص']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.success("✅ جميع المذكرات مسجلة أو مقترحة!")

# ============================================================
# فضاء الإدارة
# ============================================================
elif st.session_state.user_type == "admin":
    if not st.session_state.logged_in:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("رجوع", key="back_admin"):
                st.session_state.user_type = None
                st.rerun()
        
        st.markdown("<h2>⚙️ فضاء الإدارة</h2>", unsafe_allow_html=True)
        
        with st.form("admin_login"):
            u = st.text_input("اسم المستخدم")
            p = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("دخول"):
                v, r = verify_admin(u, p)
                if not v: st.error(r)
                else: st.session_state.admin_user = r; st.session_state.logged_in = True; st.rerun()
    else:
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("خروج"):
                logout()
        st.header("📊 لوحة تحكم الإدارة")
        
        # --- Stats ---
        st_s = len(df_students); t_m = len(df_memos); r_m = len(df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
        a_m = t_m - r_m; t_p = len(df_prof_memos["الأستاذ"].unique())
        reg_st = df_students["رقم المذكرة"].notna().sum()
        unreg_st = st_s - reg_st
        
        st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-value">{st_s}</div>
                <div class="kpi-label">الطلاب</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{t_p}</div>
                <div class="kpi-label">الأساتذة</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{t_m}</div>
                <div class="kpi-label">إجمالي المذكرات</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{r_m}</div>
                <div class="kpi-label">مذكرات مسجلة</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{a_m}</div>
                <div class="kpi-label">مذكرات متاحة</div>
            </div>
            <div class="kpi-card" style="border-color: #10B981;">
                <div class="kpi-value" style="color: #10B981;">{reg_st}</div>
                <div class="kpi-label">طلاب مسجلين</div>
            </div>
            <div class="kpi-card" style="border-color: #F59E0B;">
                <div class="kpi-value" style="color: #F59E0B;">{unreg_st}</div>
                <div class="kpi-label">طلاب غير مسجلين</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # إضافة تبويب الطلبات
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["المذكرات", "إدارة الطلبات", "الصيانة والربط"])

        with tab1:
            st.subheader("جدول المذكرات")
            f_status = st.selectbox("تصفية:", ["الكل", "مسجلة", "متاحة"])
            if f_status == "الكل":
                d_memos = df_memos
            elif f_status == "مسجلة":
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
            else:
                d_memos = df_memos[df_memos["تم التسجيل"].astype(str).str.strip() != "نعم"]
            
            st.dataframe(d_memos, use_container_width=True, height=400)

        with tab2:
            st.subheader("إدارة الطلبات الواردة")
            
            # منطق التعديل (Modal vs List)
            if st.session_state.get('admin_edit_req'):
                # صفحة تعديل الطلب
                idx = st.session_state.admin_edit_req
                req_row = df_requests.iloc[idx]
                
                st.empty() # إخفاء القائمة
                st.markdown("<div class='card'><h2>⚖️ اتخاذ قرار للطلب</h2></div>", unsafe_allow_html=True)
                
                # عرض معلومات الطلب
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**نوع الطلب:** {req_row['نوع الطلب']}")
                    st.write(f"**الأستاذ:** {req_row['الأستاذ']}")
                    st.write(f"**رقم المذكرة:** {req_row['رقم المذكرة']}")
                    st.info(f"**تفاصيل الطلب:** {req_row['العنوان الجديد']}")
                
                with c2:
                    new_status = st.selectbox("قرار الإدارة:", 
                        ["قيد المراجعة", "مقبول", "مرفوض"], 
                        index=["قيد المراجعة", "مقبول", "مرفوض"].index(req_row['الحالة'])])
                    admin_notes = st.text_area("ملاحظات الإدارة:", value=req_row.get('ملاحظات الإدارة', ''))
                
                # الأزرار
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("💾 حفظ القرار", type="primary"):
                        # تحديث الشيت
                        # A=0, B=1, C=2, D=3 ... J=9
                        sheet_row = idx + 2
                        
                        body = {
                            "valueInputOption": "USER_ENTERED",
                            "data": [
                                {"range": f"Feuille 1!D{sheet_row}", "values": [[new_status]]}, # العمود D (الحالة)
                                {"range": f"Feuille 1!J{sheet_row}", "values": [[admin_notes]]}  # العمود J (ملاحظات الإدارة)
                            ]
                        }
                        sheets_service.spreadsheets().values().batchUpdate(spreadsheetId=REQUESTS_SHEET_ID, body=body).execute()
                        st.success("تم حفظ القرار")
                        clear_cache_and_reload()
                        del st.session_state.admin_edit_req
                        st.rerun()
                
                with col_b2:
                    if st.button("إلغاء"):
                        del st.session_state.admin_edit_req
                        st.rerun()

            else:
                # عرض الجدول
                for index, row in df_requests.iterrows():
                    c = "#10B981" if row['الحالة'] == "مقبول" else "#F59E0B"
                    
                    col1, col2, col3 = st.columns([3, 6, 1])
                    with col1:
                        st.markdown(f"""
                        <div style='background:#1E293B; padding:10px; border-radius:5px; margin-bottom:5px; border-right:3px solid {c};'>
                            <b>{row['نوع الطلب']}</b> - {row['رقم المذكرة']} <br>
                            <span style="font-size:0.9em;">{row['الوقت']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        if st.button("⚙️ اتخاذ قرار", key=f"edit_{index}"):
                            st.session_state.admin_edit_req = index
                            st.rerun()

        with tab3:
            st.subheader("الصيانة والربط الذكي (S & T)")
            st.warning("⚠️ استخدم هذا الزر لربط أرقام التسجيل لأول مرة أو لإصلاح الأخطاء.")
            if st.button("🔄 بدء عملية الربط (مع تقرير تفصيلي)", type="primary"):
                with st.spinner("جاري المعالجة... قد يستغرق وقتاً"):
                    s, m = sync_student_registration_numbers()
                    st.success(m) if s else st.info(m)
                    if s: 
                        clear_cache_and_reload()
                        st.rerun()
            
            st.markdown("---")
            if st.button("تحديث البيانات من Google Sheets"):
                with st.spinner("جاري التحديث..."):
                    clear_cache_and_reload()
                    st.success("✅ تم التحديث")
                    st.rerun()

st.markdown("---")
st.markdown('<div style="text-align:center; color:#64748B; font-size:12px; padding:20px;">© 2026 جامعة محمد البشير الإبراهيمي - كلية الحقوق</div>', unsafe_allow_html=True)
