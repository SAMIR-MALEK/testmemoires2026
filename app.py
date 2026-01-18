elif st.session_state.page == "professor_dashboard" and st.session_state.logged_in:
    
    prof = st.session_state.professor
    prof_name = str(prof['الأستاذ']).strip()
    prof_username = str(prof['إسم المستخدم']).strip()
    
    # رأس الصفحة
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<h1 style="font-size:42px; margin-bottom:0;">👨‍🏫 مرحباً الأستاذ(ة) {prof_name}</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_prof", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # تحميل بيانات المذكرات
    df_memos_fresh = load_memos()
    df_prof_memos_fresh = load_prof_memos()
    
    # جمع إحصائيات
    my_memos = df_prof_memos_fresh[df_prof_memos_fresh["الأستاذ"].astype(str).str.strip() == prof_name]
    total_memos = len(my_memos)
    registered_memos = len(my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"])
    remaining_memos = total_memos - registered_memos
    
    # عرض الإحصائيات
    st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">📊 الإحصائيات</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="big-icon">📚</div>
            <div class="stat-number">{total_memos}</div>
            <div class="stat-label">إجمالي المذكرات</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="stat-card" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%);">
            <div class="big-icon">✅</div>
            <div class="stat-number">{registered_memos}</div>
            <div class="stat-label">المذكرات المسجلة</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="stat-card" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);">
            <div class="big-icon">⏳</div>
            <div class="stat-number">{remaining_memos}</div>
            <div class="stat-label">المذكرات المتبقية</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # التبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["📝 المذكرات المسجلة", "🔑 كلمات السر", "📋 جميع المذكرات", "💬 إرسال رسالة"])
    
    # ========== التبويب الأول: المذكرات المسجلة ==========
    with tab1:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">✅ المذكرات المسجلة</h2>', unsafe_allow_html=True)
        
        registered = my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        if registered.empty:
            st.markdown('<div class="info-msg">📝 لا توجد مذكرات مسجلة حتى الآن</div>', unsafe_allow_html=True)
        else:
            for idx, row in registered.iterrows():
                memo_number = str(row.get('رقم المذكرة', '')).strip()
                student1 = str(row.get('الطالب الأول', '')).strip()
                student2 = str(row.get('الطالب الثاني', '')).strip()
                reg_date = str(row.get('تاريخ التسجيل', '')).strip()
                progress = str(row.get('نسبة التقدم', '0% - لم يبدأ')).strip()
                notes = str(row.get('ملاحظات', '')).strip()
                
                # الحصول على العنوان من شيت المذكرات
                memo_title = ""
                memo_data = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == memo_number]
                if not memo_data.empty:
                    memo_title = str(memo_data.iloc[0].get('عنوان المذكرة', '')).strip()
                
                with st.expander(f"📄 المذكرة رقم {memo_number} - {student1}" + (f" و {student2}" if student2 else ""), expanded=False):
                    st.markdown(f"**📑 العنوان:** {memo_title}")
                    st.markdown(f"**👤 الطالب الأول:** {student1}")
                    if student2:
                        st.markdown(f"**👤 الطالب الثاني:** {student2}")
                    st.markdown(f"**📅 تاريخ التسجيل:** {reg_date}")
                    
                    # شريط التقدم
                    progress_num = int(progress.split('%')[0]) if '%' in progress else 0
                    st.markdown(f'''
                    <div class="progress-container">
                        <div style="font-size:20px; font-weight:700; margin-bottom:0.5rem;">📊 نسبة التقدم</div>
                        <div style="background:#0F172A; border-radius:20px; height:40px; overflow:hidden;">
                            <div class="progress-bar" style="width:{progress_num}%; display:flex; align-items:center; justify-content:center;">
                                <span style="color:white; font-weight:900; font-size:18px;">{progress_num}%</span>
                            </div>
                        </div>
                        <div class="progress-text" style="margin-top:0.5rem;">{progress}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # تعديل العنوان
                    st.markdown("### ✏️ تعديل العنوان")
                    new_title = st.text_area("عنوان جديد:", value=memo_title, key=f"title_{idx}", height=100)
                    
                    if st.button("💾 حفظ العنوان الجديد", key=f"save_title_{idx}"):
                        if new_title.strip() and new_title.strip() != memo_title:
                            success, msg = update_memo_title(memo_number, new_title.strip(), prof_name)
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="warning-msg">⚠️ لم يتم إجراء أي تغيير</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # تحديث نسبة التقدم
                    st.markdown("### 📊 تحديث نسبة التقدم")
                    new_progress = st.selectbox("اختر المرحلة:", PROGRESS_STAGES, key=f"progress_{idx}", index=PROGRESS_STAGES.index(progress) if progress in PROGRESS_STAGES else 0)
                    
                    if st.button("💾 حفظ نسبة التقدم", key=f"save_progress_{idx}"):
                        success, msg = update_progress(memo_number, new_progress, prof_username)
                        if success:
                            st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # الملاحظات
                    st.markdown("### 📝 الملاحظات (خاصة بالأستاذ والإدارة)")
                    new_notes = st.text_area("الملاحظات:", value=notes, key=f"notes_{idx}", height=150)
                    
                    if st.button("💾 حفظ الملاحظات", key=f"save_notes_{idx}"):
                        success, msg = update_notes(memo_number, new_notes.strip(), prof_username)
                        if success:
                            st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
    
    # ========== التبويب الثاني: كلمات السر ==========
    with tab2:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">🔑 كلمات السر المخصصة</h2>', unsafe_allow_html=True)
        
        used_passwords = []
        available_passwords = []
        
        for idx, row in my_memos.iterrows():
            password = str(row.get("كلمة سر التسجيل", "")).strip()
            if password:
                is_used = str(row.get("تم التسجيل", "")).strip() == "نعم"
                memo_num = str(row.get("رقم المذكرة", "")).strip()
                
                if is_used:
                    used_passwords.append({
                        'password': password,
                        'memo': memo_num,
                        'student': str(row.get('الطالب الأول', '')).strip()
                    })
                else:
                    available_passwords.append(password)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
            st.markdown('### ✅ كلمات السر المستخدمة')
            if used_passwords:
                for item in used_passwords:
                    st.markdown(f"🔒 **{item['password']}** - مذكرة {item['memo']} ({item['student']})")
            else:
                st.markdown("لا توجد كلمات سر مستخدمة")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="info-card" style="border-left-color:#F59E0B;">', unsafe_allow_html=True)
            st.markdown('### ⏳ كلمات السر المتاحة')
            if available_passwords:
                for pwd in available_passwords:
                    st.markdown(f"🔓 **{pwd}**")
            else:
                st.markdown("لا توجد كلمات سر متاحة")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== التبويب الثالث: جميع المذكرات ==========
    with tab3:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">📋 جميع المذكرات المقترحة</h2>', unsafe_allow_html=True)
        
        for idx, row in my_memos.iterrows():
            memo_number = str(row.get('رقم المذكرة', '')).strip()
            is_registered = str(row.get("تم التسجيل", "")).strip() == "نعم"
            
            # الحصول على العنوان
            memo_title = ""
            specialty = ""
            memo_data = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == memo_number]
            if not memo_data.empty:
                memo_title = str(memo_data.iloc[0].get('عنوان المذكرة', '')).strip()
                specialty = str(memo_data.iloc[0].get('التخصص', '')).strip()
            
            status_icon = "✅" if is_registered else "⏳"
            status_text = "مسجلة" if is_registered else "متاحة"
            
            st.markdown(f'''
            <div class="memo-row">
                {status_icon} <strong>{memo_number}.</strong> {memo_title} 
                <span style="color:#94A3B8;">({specialty})</span>
                <span style="float:left; color:{'#10B981' if is_registered else '#F59E0B'}; font-weight:700;">{status_text}</span>
            </div>
            ''', unsafe_allow_html=True)
    
    # ========== التبويب الرابع: إرسال رسالة ==========
    with tab4:
        st.markdown('<h2 style="font-size:28px; margin:1.5rem 0;">💬 إرسال رسالة للطالب</h2>', unsafe_allow_html=True)
        
        registered = my_memos[my_memos["تم التسجيل"].astype(str).str.strip() == "نعم"]
        
        if registered.empty:
            st.markdown('<div class="info-msg">📝 لا توجد مذكرات مسجلة لإرسال رسائل</div>', unsafe_allow_html=True)
        else:
            # اختيار المذكرة
            memo_options = []
            for idx, row in registered.iterrows():
                memo_num = str(row.get('رقم المذكرة', '')).strip()
                student = str(row.get('الطالب الأول', '')).strip()
                memo_options.append(f"{memo_num} - {student}")
            
            selected_memo = st.selectbox("📄 اختر المذكرة:", memo_options, key="msg_memo")
            
            message_text = st.text_area("💬 الرسالة:", height=200, key="message_content", placeholder="اكتب رسالتك هنا...")
            
            if st.button("📧 إرسال الرسالة", type="primary", use_container_width=True):
                if not message_text.strip():
                    st.markdown('<div class="error-msg">⚠️ يرجى كتابة رسالة</div>', unsafe_allow_html=True)
                else:
                    # استخراج رقم المذكرة
                    selected_memo_num = selected_memo.split(' - ')[0].strip()
                    
                    # الحصول على بيانات الطالب
                    df_students_fresh = load_students()
                    student_data = df_students_fresh[df_students_fresh["رقم المذكرة"].astype(str).str.strip() == selected_memo_num]
                    
                    if not student_data.empty:
                        emails_sent = 0
                        for idx, student in student_data.iterrows():
                            student_email = str(student.get('البريد المهني', '')).strip()
                            student_name = f"{student['اللقب']} {student['الإسم']}"
                            
                            if student_email and '@' in student_email:
                                if send_message_to_student(student_email, student_name, prof_name, message_text.strip()):
                                    emails_sent += 1
                        
                        if emails_sent > 0:
                            st.markdown(f'<div class="success-msg">✅ تم إرسال الرسالة بنجاح إلى {emails_sent} طالب/طلاب</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="error-msg">❌ فشل إرسال الرسالة. تحقق من البريد الإلكتروني</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-msg">❌ لم يتم العثور على بيانات الطالب</div>', unsafe_allow_html=True)

# ---------------- فضاء الطالب ----------------
elif st.session_state.page == "student_space" and st.session_state.logged_in:
    
    s1 = st.session_state.student1
    s2 = st.session_state.student2
    
    # رأس الصفحة
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<h1 style="font-size:42px; margin-bottom:0;">🎓 مرحباً {s1["اللقب"]} {s1["الإسم"]}</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🚪 خروج", key="logout_student", use_container_width=True):
            logout()
    
    st.markdown("---")
    
    # معلومات الطالب
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown(f"**👤 الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
    st.markdown(f"**🎓 التخصص:** {s1['التخصص']}")
    if s2 is not None:
        st.markdown(f"**👤 الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # التحقق من وجود مذكرة مسجلة
    note_number = str(s1.get('رقم المذكرة', '')).strip()
    
    if note_number:
        # ========== الطالب مسجل - عرض معلومات المذكرة ==========
        df_memos_fresh = load_memos()
        df_prof_memos_fresh = load_prof_memos()
        
        memo_info = df_memos_fresh[df_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number]
        
        if not memo_info.empty:
            memo_info = memo_info.iloc[0]
            prof_name = str(memo_info['الأستاذ']).strip()
            
            # الحصول على نسبة التقدم من شيت الأساتذة
            prof_memo_data = df_prof_memos_fresh[
                (df_prof_memos_fresh["رقم المذكرة"].astype(str).str.strip() == note_number)
            ]
            
            progress = "0% - لم يبدأ"
            if not prof_memo_data.empty:
                progress = str(prof_memo_data.iloc[0].get('نسبة التقدم', '0% - لم يبدأ')).strip()
            
            st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">✅ مذكرتك المسجلة</h2>', unsafe_allow_html=True)
            
            st.markdown('<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
            st.markdown(f"### 📄 المذكرة رقم {memo_info['رقم المذكرة']}")
            st.markdown(f"**📑 العنوان:** {memo_info['عنوان المذكرة']}")
            st.markdown(f"**👨‍🏫 الأستاذ المشرف:** {memo_info['الأستاذ']}")
            st.markdown(f"**🎯 التخصص:** {memo_info['التخصص']}")
            st.markdown(f"**📅 تاريخ التسجيل:** {memo_info.get('تاريخ التسجيل', '')}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # شريط التقدم
            st.markdown('<h2 style="font-size:28px; margin:2rem 0 1rem 0;">📊 نسبة التقدم</h2>', unsafe_allow_html=True)
            
            progress_num = int(progress.split('%')[0]) if '%' in progress else 0
            
            st.markdown(f'''
            <div class="progress-container">
                <div style="background:#0F172A; border-radius:20px; height:50px; overflow:hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                    <div class="progress-bar" style="width:{progress_num}%; display:flex; align-items:center; justify-content:center; height:50px;">
                        <span style="color:white; font-weight:900; font-size:22px;">{progress_num}%</span>
                    </div>
                </div>
                <div class="progress-text" style="margin-top:1rem; font-size:26px;">{progress}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('<div class="info-msg" style="margin-top:2rem;">', unsafe_allow_html=True)
            st.markdown("### ℹ️ ملاحظات هامة")
            st.markdown("• يتم تحديث نسبة التقدم من قبل الأستاذ المشرف")
            st.markdown("• في حالة وجود أي استفسار، يرجى التواصل مباشرة مع الأستاذ المشرف")
            st.markdown("• تابع بريدك الإلكتروني لتلقي الرسائل والتحديثات")
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.markdown('<div class="error-msg">⚠️ لم يتم العثور على معلومات المذكرة. يرجى تحديث الصفحة.</div>', unsafe_allow_html=True)
            if st.button("🔄 تحديث الصفحة", use_container_width=True):
                clear_cache()
                time.sleep(1)
                st.rerun()
    
    else:
        # ========== الطالب غير مسجل - نموذج التسجيل ==========
        st.markdown('<h2 style="font-size:32px; margin:2rem 0 1rem 0;">📝 تسجيل مذكرة جديدة</h2>', unsafe_allow_html=True)
        
        st.markdown('<div class="warning-msg">', unsafe_allow_html=True)
        st.markdown("### ⚠️ تنبيه هام")
        st.markdown("• اختر الأستاذ المشرف والمذكرة بعناية")
        st.markdown("• بعد التأكيد النهائي، لن تتمكن من تغيير المذكرة")
        st.markdown("• تأكد من صحة رقم المذكرة وكلمة سر المشرف")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # اختيار الأستاذ
        all_profs = sorted(df_memos["الأستاذ"].dropna().unique())
        selected_prof = st.selectbox("🧑‍🏫 اختر الأستاذ المشرف:", [""] + all_profs, key="select_prof")
        
        if selected_prof:
            student_specialty = s1["التخصص"]
            available_memos_df = df_memos[
                (df_memos["الأستاذ"].astype(str).str.strip() == selected_prof.strip()) &
                (df_memos["التخصص"].astype(str).str.strip() == student_specialty.strip()) &
                (df_memos["تم التسجيل"].astype(str).str.strip() != "نعم")
            ][["رقم المذكرة", "عنوان المذكرة"]]
            
            if not available_memos_df.empty:
                st.markdown(f'<div class="info-card" style="border-left-color:#10B981;">', unsafe_allow_html=True)
                st.markdown(f'<h3 style="color:#10B981; font-size:24px;">✅ المذكرات المتاحة في تخصصك ({student_specialty})</h3>', unsafe_allow_html=True)
                
                for idx, row in available_memos_df.iterrows():
                    st.markdown(f"**{row['رقم المذكرة']}.** {row['عنوان المذكرة']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-msg">❌ لا توجد مذكرات متاحة لهذا الأستاذ في تخصصك</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # إدخال البيانات
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.note_number = st.text_input(
                "📄 رقم المذكرة", 
                value=st.session_state.note_number,
                max_chars=20,
                key="note_num_input"
            )
        with col2:
            st.session_state.prof_password = st.text_input(
                "🔑 كلمة سر المشرف", 
                type="password",
                key="prof_pass_input",
                max_chars=50
            )
        
        # نموذج التأكيد
        if not st.session_state.show_confirmation:
            if st.button("📝 المتابعة للتأكيد", type="primary", use_container_width=True):
                if not st.session_state.note_number or not st.session_state.prof_password:
                    st.markdown('<div class="error-msg">⚠️ يرجى إدخال رقم المذكرة وكلمة سر المشرف</div>', unsafe_allow_html=True)
                else:
                    st.session_state.show_confirmation = True
                    st.rerun()
        else:
            st.markdown('<div class="warning-msg">', unsafe_allow_html=True)
            st.markdown("### ⚠️ تأكيد نهائي")
            st.markdown(f"**📄 رقم المذكرة:** {st.session_state.note_number}")
            st.markdown(f"**👤 الطالب الأول:** {s1['اللقب']} {s1['الإسم']}")
            if s2 is not None:
                st.markdown(f"**👤 الطالب الثاني:** {s2['اللقب']} {s2['الإسم']}")
            st.markdown("**🚨 تنبيه:** بعد التأكيد، لن تتمكن من تغيير المذكرة!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ تأكيد نهائي", type="primary", use_container_width=True):
                    valid_memo, prof_row, error_msg = verify_professor_password(
                        st.session_state.note_number, 
                        st.session_state.prof_password, 
                        df_memos, 
                        df_prof_memos
                    )
                    
                    if not valid_memo:
                        st.markdown(f'<div class="error-msg">{error_msg}</div>', unsafe_allow_html=True)
                        st.session_state.show_confirmation = False
                    else:
                        with st.spinner('⏳ جاري تسجيل المذكرة...'):
                            success, message = update_registration(
                                st.session_state.note_number, 
                                s1, 
                                s2
                            )
                        
                        if success:
                            st.markdown(f'<div class="success-msg">{message}</div>', unsafe_allow_html=True)
                            st.balloons()
                            
                            clear_cache()
                            st.session_state.show_confirmation = False
                            
                            # إعادة تحميل بيانات الطالب
                            time.sleep(2)
                            df_students_updated = load_students()
                            st.session_state.student1 = df_students_updated[
                                df_students_updated["اسم المستخدم"].astype(str).str.strip() == s1['اسم المستخدم'].strip()
                            ].iloc[0]
                            
                            if s2 is not None:
                                st.session_state.student2 = df_students_updated[
                                    df_students_updated["اسم المستخدم"].astype(str).str.strip() == s2['اسم المستخدم'].strip()
                                ].iloc[0]
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="error-msg">{message}</div>', unsafe_allow_html=True)
                            st.session_state.show_confirmation = False
            
            with col2:
                if st.button("❌ إلغاء", use_container_width=True):
                    st.session_state.show_confirmation = False
                    st.rerun()

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("""
    <div style='text-align:center; color:#64748B; font-size:16px; padding:30px; background:rgba(30, 41, 59, 0.5); border-radius:16px; margin-top:3rem;'>
        <p style='font-size:18px; font-weight:700; color:#F1F5F9; margin-bottom:1rem;'>© 2026 جامعة محمد البشير الإبراهيمي</p>
        <p style='font-size:16px; color:#94A3B8;'>كلية الحقوق والعلوم السياسية</p>
        <p style='margin-top:1rem; font-size:14px;'>للاستفسار يرجى الاتصال بمكتب فريق التكوين</p>
    </div>
""", unsafe_allow_html=True)