import React, { useState, useEffect } from 'react';
import { Users, BookOpen, CheckCircle, Clock, Phone, TrendingUp, Award, AlertCircle, LogOut, Search, Filter } from 'lucide-react';

const App = () => {
  const [userType, setUserType] = useState(null);
  const [professorAuth, setProfessorAuth] = useState({ username: '', password: '' });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [phone1, setPhone1] = useState('');
  const [phone2, setPhone2] = useState('');
  const [selectedThesis, setSelectedThesis] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [professorData, setProfessorData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [theses, setTheses] = useState([]);

  const validatePhone = (phone) => {
    const phoneRegex = /^(05|06|07)\d{8}$/;
    return phoneRegex.test(phone);
  };

  useEffect(() => {
    if (userType === 'student') {
      loadTheses();
    }
  }, [userType]);

  const loadTheses = async () => {
    try {
      const csvData = await window.fs.readFile('المذكرات-الأساتذة.csv', { encoding: 'utf8' });
      const Papa = await import('https://cdn.jsdelivr.net/npm/papaparse@5.4.1/+esm');
      const parsedData = Papa.parse(csvData, { header: true, skipEmptyLines: true });
      
      const availableTheses = parsedData.data.filter(row => 
        row['حالة التسجيل']?.trim() === 'متاحة'
      );
      
      setTheses(availableTheses);
    } catch (error) {
      console.error('Error loading theses:', error);
    }
  };

  const handleStudentRegistration = async () => {
    if (!firstName || !lastName || !password || !selectedThesis || !phone1) {
      setMessage('⚠️ يرجى ملء جميع الحقول المطلوبة');
      return;
    }

    if (!validatePhone(phone1)) {
      setMessage('⚠️ رقم الهاتف الأول غير صحيح (يجب أن يبدأ بـ 05 أو 06 أو 07 ويحتوي على 10 أرقام)');
      return;
    }

    if (phone2 && !validatePhone(phone2)) {
      setMessage('⚠️ رقم الهاتف الثاني غير صحيح');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const thesesResponse = await window.fs.readFile('المذكرات-الأساتذة.csv', { encoding: 'utf8' });
      const Papa = await import('https://cdn.jsdelivr.net/npm/papaparse@5.4.1/+esm');
      const thesesData = Papa.parse(thesesResponse, { header: true, skipEmptyLines: true });
      
      const thesis = thesesData.data.find(t => 
        t['عنوان المذكرة']?.trim() === selectedThesis.trim()
      );

      if (!thesis) {
        setMessage('❌ المذكرة غير موجودة');
        setLoading(false);
        return;
      }

      const status = thesis['حالة التسجيل']?.trim();
      const savedPassword = thesis['كلمة السر']?.trim();

      if (status === 'مسجلة') {
        setMessage('❌ هذه المذكرة مسجلة بالفعل');
        setLoading(false);
        return;
      }

      if (password !== savedPassword) {
        setMessage('❌ كلمة السر غير صحيحة');
        setLoading(false);
        return;
      }

      const phoneInfo = phone2 ? `${phone1} / ${phone2}` : phone1;
      const studentName = `${firstName.trim()} ${lastName.trim()}`;
      
      setMessage(`✅ تم تسجيل المذكرة بنجاح!\n\nالطالب: ${studentName}\nالهاتف: ${phoneInfo}\nالمذكرة: ${selectedThesis}`);
      
      setFirstName('');
      setLastName('');
      setPassword('');
      setPhone1('');
      setPhone2('');
      setSelectedThesis('');
      
    } catch (error) {
      setMessage('❌ حدث خطأ في قراءة البيانات');
      console.error(error);
    }

    setLoading(false);
  };

  const handleProfessorLogin = async () => {
    if (!professorAuth.username || !professorAuth.password) {
      setMessage('⚠️ يرجى إدخال اسم المستخدم وكلمة المرور');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const thesesResponse = await window.fs.readFile('المذكرات-الأساتذة.csv', { encoding: 'utf8' });
      const Papa = await import('https://cdn.jsdelivr.net/npm/papaparse@5.4.1/+esm');
      const thesesData = Papa.parse(thesesResponse, { header: true, skipEmptyLines: true });
      
      const professor = thesesData.data.find(row => 
        row['إسم المستخدم']?.trim() === professorAuth.username.trim() &&
        row['كلمة المرور']?.trim() === professorAuth.password.trim()
      );

      if (!professor) {
        setMessage('❌ اسم المستخدم أو كلمة المرور غير صحيحة');
        setLoading(false);
        return;
      }

      const professorName = professor['الأستاذ']?.trim();
      const professorTheses = thesesData.data.filter(t => 
        t['الأستاذ']?.trim() === professorName
      );

      const stats = {
        total: professorTheses.length,
        registered: professorTheses.filter(t => t['حالة التسجيل']?.trim() === 'مسجلة').length,
        available: professorTheses.filter(t => t['حالة التسجيل']?.trim() === 'متاحة').length,
        theses: professorTheses.map(t => ({
          title: t['عنوان المذكرة'],
          status: t['حالة التسجيل'],
          password: t['كلمة السر'],
          student: t['الطالب'] || '-',
          phones: t['أرقام الهواتف'] || '-',
          date: t['تاريخ التسجيل'] || '-'
        }))
      };

      setProfessorData({ name: professorName, stats });
      setIsAuthenticated(true);
      
    } catch (error) {
      setMessage('❌ حدث خطأ في تسجيل الدخول');
      console.error(error);
    }

    setLoading(false);
  };

  const handleLogout = () => {
    setUserType(null);
    setIsAuthenticated(false);
    setProfessorAuth({ username: '', password: '' });
    setProfessorData(null);
    setMessage('');
  };

  if (!userType) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4">منصة إدارة المذكرات</h1>
            <p className="text-xl text-blue-200">اختر نوع الحساب للمتابعة</p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div 
              onClick={() => setUserType('student')}
              className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:bg-white/20 border border-white/20"
            >
              <div className="text-center">
                <div className="bg-gradient-to-r from-blue-500 to-cyan-500 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
                  <BookOpen className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">طالب</h2>
                <p className="text-blue-200 text-lg">تسجيل وإدارة المذكرات</p>
              </div>
            </div>

            <div 
              onClick={() => setUserType('professor')}
              className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 cursor-pointer transform transition-all hover:scale-105 hover:bg-white/20 border border-white/20"
            >
              <div className="text-center">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Award className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">أستاذ</h2>
                <p className="text-purple-200 text-lg">لوحة التحكم والإحصائيات</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (userType === 'professor') {
    if (!isAuthenticated) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <button
              onClick={handleLogout}
              className="mb-6 text-white/70 hover:text-white flex items-center gap-2 transition-colors"
            >
              ← الرجوع
            </button>
            
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 border border-white/20">
              <div className="text-center mb-8">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Award className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-2">تسجيل دخول الأستاذ</h2>
                <p className="text-purple-200">أدخل بيانات الدخول الخاصة بك</p>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-white mb-2 font-semibold">اسم المستخدم</label>
                  <input
                    type="text"
                    value={professorAuth.username}
                    onChange={(e) => setProfessorAuth({...professorAuth, username: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="أدخل اسم المستخدم"
                  />
                </div>

                <div>
                  <label className="block text-white mb-2 font-semibold">كلمة المرور</label>
                  <input
                    type="password"
                    value={professorAuth.password}
                    onChange={(e) => setProfessorAuth({...professorAuth, password: e.target.value})}
                    className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    placeholder="أدخل كلمة المرور"
                  />
                </div>

                <button
                  onClick={handleProfessorLogin}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 rounded-xl font-bold text-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
                >
                  {loading ? 'جاري التحقق...' : 'تسجيل الدخول'}
                </button>

                {message && (
                  <div className="mt-4 p-4 rounded-xl bg-white/20 border border-white/30">
                    <p className="text-white text-center whitespace-pre-line">{message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    const filteredTheses = professorData.stats.theses.filter(t => {
      const matchesSearch = t.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           t.student.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterStatus === 'all' || t.status === filterStatus;
      return matchesSearch && matchesFilter;
    });

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">لوحة التحكم</h1>
              <p className="text-purple-200 text-xl">مرحباً {professorData.name}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-xl border border-white/20 transition-all"
            >
              <LogOut className="w-5 h-5" />
              تسجيل الخروج
            </button>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <BookOpen className="w-12 h-12 opacity-80" />
                <div className="text-right">
                  <p className="text-blue-100 text-sm">إجمالي المذكرات</p>
                  <p className="text-4xl font-bold">{professorData.stats.total}</p>
                </div>
              </div>
              <div className="h-2 bg-white/30 rounded-full">
                <div className="h-full bg-white rounded-full" style={{width: '100%'}}></div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <CheckCircle className="w-12 h-12 opacity-80" />
                <div className="text-right">
                  <p className="text-green-100 text-sm">المذكرات المسجلة</p>
                  <p className="text-4xl font-bold">{professorData.stats.registered}</p>
                </div>
              </div>
              <div className="h-2 bg-white/30 rounded-full">
                <div 
                  className="h-full bg-white rounded-full" 
                  style={{width: `${(professorData.stats.registered / professorData.stats.total * 100)}%`}}
                ></div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-amber-500 rounded-2xl p-6 text-white">
              <div className="flex items-center justify-between mb-4">
                <Clock className="w-12 h-12 opacity-80" />
                <div className="text-right">
                  <p className="text-orange-100 text-sm">المذكرات المتاحة</p>
                  <p className="text-4xl font-bold">{professorData.stats.available}</p>
                </div>
              </div>
              <div className="h-2 bg-white/30 rounded-full">
                <div 
                  className="h-full bg-white rounded-full" 
                  style={{width: `${(professorData.stats.available / professorData.stats.total * 100)}%`}}
                ></div>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-white/20">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="relative">
                <Search className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/50 w-5 h-5" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="البحث عن مذكرة أو طالب..."
                  className="w-full pr-12 pl-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400"
                />
              </div>
              
              <div className="relative">
                <Filter className="absolute right-4 top-1/2 transform -translate-y-1/2 text-white/50 w-5 h-5" />
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full pr-12 pl-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white focus:outline-none focus:ring-2 focus:ring-purple-400 appearance-none"
                >
                  <option value="all" className="bg-purple-900">جميع الحالات</option>
                  <option value="متاحة" className="bg-purple-900">متاحة</option>
                  <option value="مسجلة" className="bg-purple-900">مسجلة</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-white/10 border-b border-white/20">
                    <th className="px-6 py-4 text-right text-white font-bold">عنوان المذكرة</th>
                    <th className="px-6 py-4 text-right text-white font-bold">الحالة</th>
                    <th className="px-6 py-4 text-right text-white font-bold">الطالب</th>
                    <th className="px-6 py-4 text-right text-white font-bold">أرقام الهواتف</th>
                    <th className="px-6 py-4 text-right text-white font-bold">كلمة السر</th>
                    <th className="px-6 py-4 text-right text-white font-bold">تاريخ التسجيل</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTheses.map((thesis, index) => (
                    <tr key={index} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                      <td className="px-6 py-4 text-white">{thesis.title}</td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          thesis.status === 'مسجلة' 
                            ? 'bg-green-500/20 text-green-300 border border-green-500/50' 
                            : 'bg-orange-500/20 text-orange-300 border border-orange-500/50'
                        }`}>
                          {thesis.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-white">{thesis.student}</td>
                      <td className="px-6 py-4 text-white">
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 text-blue-300" />
                          {thesis.phones}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-white">
                        <code className="bg-white/10 px-3 py-1 rounded border border-white/20">
                          {thesis.password}
                        </code>
                      </td>
                      <td className="px-6 py-4 text-white">{thesis.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {filteredTheses.length === 0 && (
              <div className="text-center py-12">
                <AlertCircle className="w-16 h-16 text-white/30 mx-auto mb-4" />
                <p className="text-white/50 text-lg">لا توجد نتائج</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto py-8">
        <button
          onClick={handleLogout}
          className="mb-6 text-white/70 hover:text-white flex items-center gap-2 transition-colors"
        >
          ← الرجوع
        </button>

        <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-white/20">
          <div className="text-center mb-8">
            <div className="bg-gradient-to-r from-blue-500 to-cyan-500 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white mb-2">تسجيل المذكرات</h1>
            <p className="text-blue-200 text-lg">قم بملء البيانات لتسجيل مذكرتك</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-white mb-2 font-semibold">الاسم</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="أدخل اسمك"
              />
            </div>

            <div>
              <label className="block text-white mb-2 font-semibold">اللقب</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="أدخل لقبك"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-white mb-2 font-semibold flex items-center gap-2">
                <Phone className="w-4 h-4" />
                رقم الهاتف الأول *
              </label>
              <input
                type="tel"
                value={phone1}
                onChange={(e) => setPhone1(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="0797605895"
                maxLength="10"
              />
              {phone1 && !validatePhone(phone1) && (
                <p className="text-red-300 text-sm mt-1">⚠️ يجب أن يبدأ بـ 05 أو 06 أو 07</p>
              )}
            </div>

            <div>
              <label className="block text-white mb-2 font-semibold flex items-center gap-2">
                <Phone className="w-4 h-4" />
                رقم الهاتف الثاني (اختياري)
              </label>
              <input
                type="tel"
                value={phone2}
                onChange={(e) => setPhone2(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="0612345678"
                maxLength="10"
              />
              {phone2 && !validatePhone(phone2) && (
                <p className="text-red-300 text-sm mt-1">⚠️ يجب أن يبدأ بـ 05 أو 06 أو 07</p>
              )}
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-white mb-2 font-semibold">اختر المذكرة</label>
            <select
              value={selectedThesis}
              onChange={(e) => setSelectedThesis(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white focus:outline-none focus:ring-2 focus:ring-blue-400 appearance-none"
            >
              <option value="" className="bg-purple-900">-- اختر مذكرة --</option>
              {theses.map((thesis, index) => (
                <option key={index} value={thesis['عنوان المذكرة']} className="bg-purple-900">
                  {thesis['عنوان المذكرة']}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-white mb-2 font-semibold">كلمة السر</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/20 border border-white/30 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="أدخل كلمة السر"
            />
          </div>

          <button
            onClick={handleStudentRegistration}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white py-4 rounded-xl font-bold text-lg hover:from-blue-600 hover:to-cyan-600 transition-all disabled:opacity-50 shadow-lg"
          >
            {loading ? 'جاري التسجيل...' : 'تسجيل المذكرة'}
          </button>

          {message && (
            <div className={`mt-6 p-4 rounded-xl border ${
              message.includes('✅') 
                ? 'bg-green-500/20 border-green-500/50' 
                : 'bg-red-500/20 border-red-500/50'
            }`}>
              <p className="text-white text-center whitespace-pre-line">{message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
